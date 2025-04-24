import com.amazonaws.services.secretsmanager.AWSSecretsManager;
import com.amazonaws.services.secretsmanager.model.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;

public class SetSecretHandler {
    private static final Logger logger = LoggerFactory.getLogger(SetSecretHandler.class);

    public void setSecret(AWSSecretsManager secretsManager, String arn, String token) {
        try {
            // Retrieve current and pending secret dictionaries
            SecretDictionary currentDict = getSecretDict(secretsManager, arn, "AWSCURRENT");
            SecretDictionary pendingDict = getSecretDict(secretsManager, arn, "AWSPENDING", token);

            // Try to connect with the pending secret
            Connection conn = getConnection(pendingDict);
            if (conn != null) {
                conn.close();
                logger.info("setSecret: AWSPENDING secret is already set as password in PostgreSQL DB for secret arn {}", arn);
                return;
            }

            // Validate username and host
            if (!getAltUsername(currentDict.getUsername()).equals(pendingDict.getUsername())) {
                throw new IllegalArgumentException(String.format(
                        "Attempting to modify user %s other than current user or clone %s",
                        pendingDict.getUsername(), currentDict.getUsername()));
            }

            if (!currentDict.getHost().equals(pendingDict.getHost())) {
                throw new IllegalArgumentException(String.format(
                        "Attempting to modify user for host %s other than current host %s",
                        pendingDict.getHost(), currentDict.getHost()));
            }

            // Validate AWSCURRENT secret by logging in
            conn = getConnection(currentDict);
            if (conn == null) {
                throw new IllegalArgumentException(String.format(
                        "Unable to log into database using current credentials for secret %s", arn));
            }
            conn.close();

            // Fetch master secret
            String masterArn = currentDict.getMasterArn();
            SecretDictionary masterDict = getSecretDict(secretsManager, masterArn, "AWSCURRENT", null, true);
            masterDict.setDbName(currentDict.getDbName());

            if (!currentDict.getHost().equals(masterDict.getHost()) &&
                    !isRdsReplicaDatabase(currentDict, masterDict)) {
                throw new IllegalArgumentException(String.format(
                        "Current database host %s is not the same host as/rds replica of master %s",
                        currentDict.getHost(), masterDict.getHost()));
            }

            // Log in with master credentials
            conn = getConnection(masterDict);
            if (conn == null) {
                throw new IllegalArgumentException(String.format(
                        "Unable to log into database using credentials in master secret %s", masterArn));
            }

            // Set the password for the pending user
            try (PreparedStatement stmt = conn.prepareStatement("SELECT quote_ident(?)")) {
                stmt.setString(1, pendingDict.getUsername());
                ResultSet rs = stmt.executeQuery();
                rs.next();
                String pendingUsername = rs.getString(1);

                stmt.setString(1, currentDict.getUsername());
                rs = stmt.executeQuery();
                rs.next();
                String currentUsername = rs.getString(1);

                stmt.execute("SELECT 1 FROM pg_roles WHERE rolname = ?", pendingDict.getUsername());
                rs = stmt.executeQuery();
                if (!rs.next()) {
                    stmt.execute(String.format("CREATE ROLE %s WITH LOGIN PASSWORD ?", pendingUsername),
                            pendingDict.getPassword());
                    stmt.execute(String.format("GRANT %s TO %s", currentUsername, pendingUsername));
                } else {
                    stmt.execute(String.format("ALTER USER %s WITH PASSWORD ?", pendingUsername),
                            pendingDict.getPassword());
                }

                conn.commit();
                logger.info("setSecret: Successfully set password for {} in PostgreSQL DB for secret arn {}.",
                        pendingDict.getUsername(), arn);
            } finally {
                conn.close();
            }
        } catch (Exception e) {
            logger.error("setSecret: Error occurred while setting secret", e);
            throw new RuntimeException(e);
        }
    }

    // Helper methods like getSecretDict, getConnection, getAltUsername, and isRdsReplicaDatabase
    // should be implemented here or imported from other utility classes.
}
