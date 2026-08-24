import logging
from neo4j import GraphDatabase, exceptions
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseConnection:
    _instance = None

    def __init__(self):
        self.driver = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = DatabaseConnection()
        return cls._instance

    def connect(self):
        if self.driver is not None:
            return self.driver

        if not Config.COGNODB_URI or not Config.COGNODB_PASSWORD:
            logger.warning("COGNODB_URI or COGNODB_PASSWORD missing from environment variables.")
            return None

        try:
            self.driver = GraphDatabase.driver(
                Config.COGNODB_URI,
                auth=(Config.COGNODB_USERNAME, Config.COGNODB_PASSWORD),
                max_connection_lifetime=Config.MAX_CONNECTION_LIFETIME,
                max_connection_pool_size=Config.MAX_CONNECTION_POOL_SIZE,
                connection_timeout=Config.CONNECTION_TIMEOUT
            )
            # Verify connectivity
            self.driver.verify_connectivity()
            logger.info("Successfully connected to CognoDB!")
            return self.driver
        except exceptions.AuthError as e:
            logger.error(f"Authentication failed for CognoDB: {e}")
            self.driver = None
            return None
        except exceptions.ServiceUnavailable as e:
            logger.error(f"CognoDB server unavailable at {Config.COGNODB_URI}: {e}")
            self.driver = None
            return None
        except Exception as e:
            logger.error(f"Failed to connect to CognoDB: {e}")
            self.driver = None
            return None

    def close(self):
        if self.driver:
            try:
                self.driver.close()
                logger.info("CognoDB driver connection closed.")
            except Exception as e:
                logger.error(f"Error closing driver: {e}")
            finally:
                self.driver = None

    def execute_query(self, query, parameters=None):
        driver = self.connect()
        if not driver:
            raise ConnectionError("Database unavailable. Please check configuration credentials or connectivity.")

        parameters = parameters or {}
        try:
            with driver.session() as session:
                result = session.run(query, parameters)
                # Convert records to dictionary list before session closes
                records = [record.data() for record in result]
                return records
        except exceptions.CypherSyntaxError as e:
            logger.error(f"Cypher syntax error: {e}")
            raise ValueError(f"Invalid query syntax: {e}")
        except exceptions.Neo4jError as e:
            logger.error(f"Neo4j/CognoDB execution error: {e}")
            raise RuntimeError(f"Database error: {e}")
        except Exception as e:
            logger.error(f"Unexpected database query error: {e}")
            raise e

def get_db():
    return DatabaseConnection.get_instance()

def close_db(e=None):
    db = DatabaseConnection.get_instance()
    db.close()