import logging
from pythonosc import dispatcher, osc_server
from music_gen.controllers import AbletonMetaController

#TODO: put all logs in a file
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def update_valence_handler(unused_addr, args, valence):
    controller = args[0]
    logger.debug("Received valence: %f", valence)
    controller.update_valence(valence)

def update_arousal_handler(unused_addr, args, arousal):
    controller = args[0]
    logger.debug("Received arousal: %f", arousal)
    controller.update_arousal(arousal)
    
def main():
    controller = AbletonMetaController()
    controller.setup()

    disp = dispatcher.Dispatcher()
    disp.map("/x", update_valence_handler, controller)
    disp.map("/y", update_arousal_handler, controller)

    server = osc_server.ThreadingOSCUDPServer(("0.0.0.0", 5005), disp)
    logger.info("Serving on %s:%d", server.server_address[0], server.server_address[1])

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down server...")
        controller.stop()
        server.shutdown()

if __name__ == "__main__":
    main()
