import os
from dpsn_client.client import DpsnClient, DPSNError
from datetime import datetime
from game_sdk.game.custom_types import Function, Argument, FunctionResultStatus
from typing import Dict, Any, Callable, Tuple, Optional
import json
import logging
# Configure logging for the plugin (optional, but good practice)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("DpsnPlugin")

# {{ Add a custom exception for initialization errors }}
class DpsnInitializationError(Exception):
    """Custom exception for DPSN initialization failures."""
    pass

class DpsnPlugin:
    """
    DPSN Plugin using the updated DpsnClient for handling connections,
    subscriptions, and message handling.
    """

    def __init__(self,
                dpsn_url:Optional[str] = os.getenv("DPSN_URL"),
                pvt_key:Optional[str] = os.getenv("PVT_KEY")
                 ):
        self.dpsn_url = dpsn_url
        self.pvt_key = pvt_key
        if not self.dpsn_url or not self.pvt_key:
            raise ValueError("DPSN_URL and PVT_KEY are required.")

        # {{ Create the client instance here, but don't connect yet }}
        self.client: DpsnClient | None = None 
        try:
            if self.dpsn_url and self.pvt_key:
                chain_options = {
                    "network": "testnet", # Consider making configurable
                    "wallet_chain_type": "ethereum"
                }
                connection_options = {"ssl": True} # Consider making configurable
                
                logger.info(f"Creating DpsnClient instance for {self.dpsn_url}")
                self.client = DpsnClient(
                    dpsn_url=self.dpsn_url,
                    private_key=self.pvt_key,
                    chain_options=chain_options,
                    connection_options=connection_options
                )
                # Setup internal error handler early
                self.client.on_error += self._handle_client_error
            else:
                 # Client remains None if credentials missing
                 logger.warning("DpsnClient not created due to missing URL or Key.")

        except Exception as e:
            logger.exception("Unexpected error during DpsnClient instantiation:")
            self.client = None # Ensure client is None on instantiation error
        
        # {{ Add initialization flag }}
        self._initialized = False 
        self.message_callback: Callable[[Dict[str, Any]], None] | None = None

       
        self._functions = {
            "subscribe": Function(
                fn_name="subscribe_to_topic",
                fn_description="Subscribe to a DPSN topic to receive messages",
                args=[
                    Argument(
                        name="topic",
                        description="The DPSN topic to subscribe to",
                        type="string",
                        required=True
                    )
                ],
                hint="Subscribes to a specific DPSN topic to receive messages. Will initialize connection if needed.",
                executable=self.subscribe # Keep executable pointing to the public method
            ),
            "unsubscribe": Function(
                fn_name="unsubscribe_to_topic",
                fn_description="unsubscribe to a DPSN topic to stop receiving messages",
                args=[
                    Argument(
                        name="topic",
                        description="The DPSN topic to unsubscribe to",
                        type="string",
                        required=True
                    )
                ],
                hint="Unsubscribes from a specific DPSN topic. Will initialize connection if needed.",
                executable=self.unsubscribe
            ),
            "shutdown": Function(
                fn_name="shutdown",
                fn_description="Shutdown DPSN client connection",
                args=[],
                hint="Disconnects the DPSN client gracefully.",
                executable=self.shutdown
            )
        }

    def get_function(self, fn_name: str) -> Function:
        """Get a specific function by name"""
        if fn_name not in self._functions:
            logger.error(f"Function '{fn_name}' not found in DpsnPlugin")
            raise ValueError(f"Function '{fn_name}' not found")
        return self._functions[fn_name]

    # {{ New private method to handle initialization logic }}
    def _ensure_initialized(self):
        """
        Ensures the DpsnClient is initialized. Runs initialization logic only once.
        Raises DpsnInitializationError on failure.
        """
        if self._initialized:
            return # Already initialized

        if not self.client:
             logger.error("Cannot initialize: DpsnClient instance was not created (likely missing credentials).")
             raise DpsnInitializationError("Client not configured (missing URL/Key).")
             
        # Check if already connected (e.g., if init was called externally somehow)
        if self.client.dpsn_broker and self.client.dpsn_broker.is_connected():
            logger.info("Client already connected. Marking as initialized.")
            self._initialized = True
            return

        logger.info("Initializing DpsnClient connection (first time)...")
        try:
            # Perform the actual initialization / connection
            self.client.init({
                "retry_options": {
                    "max_retries": 3,
                    "initial_delay": 1000,
                    "max_delay": 5000
                }
            })
            
            # Apply message callback if it was set before initialization finished
            if self.message_callback:
                try:
                    # Ensure handler isn't added multiple times if init is re-entrant
                    self.client.on_msg -= self.message_callback 
                except ValueError:
                    pass # Wasn't added yet
                self.client.on_msg += self.message_callback
                logger.info("Message callback applied during initialization.")

            self._initialized = True # Mark as initialized *after* successful init
            logger.info("DpsnClient initialized successfully.")

        except DPSNError as e:
            logger.error(f"DPSN Initialization Error: Code={e.code}, Msg={e.message}")
            self._initialized = False # Ensure flag is false on error
            # Raise specific error to be caught by calling function
            raise DpsnInitializationError(f"DPSNError ({e.code.name}): {e.message}") from e 
        except Exception as e:
            logger.exception("Unexpected error during DPSN initialization:")
            self._initialized = False # Ensure flag is false on error
            raise DpsnInitializationError(f"Unexpected initialization error: {str(e)}") from e

    def subscribe(self, topic: str) -> Tuple[FunctionResultStatus, str, Dict[str, Any]]:
        """Subscribes to a specific topic. Ensures client is initialized first."""
      
        try:
            self._ensure_initialized()
        except DpsnInitializationError as e:
            logger.error(f"Subscription failed for topic '{topic}' due to initialization error: {e}")
            return (FunctionResultStatus.FAILED, f"Initialization failed: {e}", {"topic": topic})

        # Existing checks (client should exist if _ensure_initialized passed)
        if not self.client or not self.client.dpsn_broker or not self.client.dpsn_broker.is_connected():
             logger.warning(f"Subscribe attempt failed for topic '{topic}': Client not connected (post-init check).")
             self._initialized = False # Reset flag if connection lost
             return (FunctionResultStatus.FAILED, "Client not connected", {"topic": topic})

        
        try:
            logger.info(f"Subscribing to topic: {topic}")
            self.client.subscribe(topic)
            logger.info(f"Successfully subscribed to topic: {topic}")
            return (FunctionResultStatus.DONE, f"Successfully subscribed to topic: {topic}", {"subscribed_topic": topic})
        except DPSNError as e:
            logger.error(f"DPSN Subscription Error for topic '{topic}': Code={e.code}, Msg={e.message}")
            return (FunctionResultStatus.FAILED, f"Subscription error ({e.code.name}): {e.message}", {"topic": topic})
        except Exception as e:
            logger.exception(f"Unexpected error during subscription to topic '{topic}':")
            return (FunctionResultStatus.FAILED, f"Unexpected subscription error: {str(e)}", {"topic": topic})

    def unsubscribe(self, topic: str) -> Tuple[FunctionResultStatus, str, Dict[str, Any]]:
        """Unsubscribes from a specific topic. Ensures client is initialized first."""
     
        try:
            self._ensure_initialized()
        except DpsnInitializationError as e:
            logger.error(f"Unsubscription failed for topic '{topic}' due to initialization error: {e}")
            return (FunctionResultStatus.FAILED, f"Initialization failed: {e}", {"topic": topic})

        # Existing checks
        if not self.client or not self.client.dpsn_broker or not self.client.dpsn_broker.is_connected():
             logger.warning(f"Unsubscribe attempt failed for topic '{topic}': Client not connected (post-init check).")
             self._initialized = False
             return (FunctionResultStatus.FAILED, "Client not connected", {"topic": topic})

        try:
            logger.info(f"Unsubscribing from topic: {topic}")
            self.client.unsubscribe(topic)
            logger.info(f"Successfully unsubscribed from topic: {topic}")
            return (FunctionResultStatus.DONE, f"Successfully unsubscribed from topic: {topic}", {"unsubscribed_topic": topic})
        except DPSNError as e:
            logger.error(f"DPSN Unsubscription Error for topic '{topic}': Code={e.code}, Msg={e.message}")
            return (FunctionResultStatus.FAILED, f"Unsubscription error ({e.code.name}): {e.message}", {"topic": topic})
        except Exception as e:
            logger.exception(f"Unexpected error during unsubscription from topic '{topic}':")
            return (FunctionResultStatus.FAILED, f"Unexpected unsubscription error: {str(e)}", {"topic": topic})


    def shutdown(self) -> Tuple[FunctionResultStatus, str, Dict[str, Any]]:
        """Disconnects the DPSN client if it was initialized."""
        if self._initialized and self.client:
            try:
                logger.info("Shutting down DpsnClient connection...")
                self.client.disconnect()
                logger.info("DpsnClient shutdown complete.")
                self._initialized = False # Reset flag after successful disconnect
                return (FunctionResultStatus.DONE, "DPSN client shutdown complete.", {})
            except DPSNError as e:
                logger.error(f"DPSN Shutdown Error: Code={e.code}, Msg={e.message}")
                self._initialized = False 
                return (FunctionResultStatus.FAILED, f"Shutdown error ({e.code.name}): {e.message}", {})
            except Exception as e:
                 logger.exception("Unexpected error during DPSN shutdown:")
                 self._initialized = False
                 return (FunctionResultStatus.FAILED, f"Unexpected shutdown error: {str(e)}", {})
        elif not self.client:
             logger.info("Shutdown called but client was never created.")
             return (FunctionResultStatus.DONE, "Client not configured.", {})
        else:
             # Client exists but was never initialized or already shut down
             logger.info("Shutdown called but client was not initialized or already shut down.")
             self._initialized = False # Ensure flag is false
             return (FunctionResultStatus.DONE, "Client was not active.", {})

    def set_message_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """
        Sets the callback function. If client is initialized, applies it immediately.
        If not initialized, stores it to be applied upon successful initialization.
        """
        logger.info(f"Setting message callback to: {callback.__name__ if hasattr(callback, '__name__') else callback}")
        
        # Remove old callback first if client exists and callback was previously set
        if self.client and self.message_callback:
            try:
                self.client.on_msg -= self.message_callback
                logger.debug("Removed previous message callback.")
            except ValueError:
                 pass # Ignore if it wasn't added or client changed

        self.message_callback = callback # Store the new callback

        # If client exists and is initialized, add the new callback immediately
        # {{ Check _initialized flag }}
        if self.client and self._initialized:
            try:
                self.client.on_msg += self.message_callback
                logger.info("Message callback applied to initialized client.")
            except Exception as e:
                 logger.exception("Failed to apply message callback to initialized client:")
        elif self.client:
             logger.info("Message callback stored and will be applied upon initialization.")
        else:
             logger.warning("Message callback stored, but client instance does not exist.")

    def _handle_client_error(self, error: DPSNError):
         """Internal handler for errors emitted by the DpsnClient."""
         logger.error(f"[DpsnClient EVENT] Error received: Code={error.code.name if hasattr(error.code, 'name') else error.code}, Msg={error.message}, Status={error.status}")
         
         if self._initialized:
            logger.warning("Marking DpsnPlugin as uninitialized due to client error.")
            self._initialized = False
         else:
             logger.warning("Client error received, but plugin was already not marked as initialized.")
    
    