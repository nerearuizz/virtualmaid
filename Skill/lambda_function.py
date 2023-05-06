
import json
import requests
from bs4 import BeautifulSoup
import logging

import ask_sdk_core.utils as ask_utils

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput

from ask_sdk_model import Response

import urllib3
from urllib3 import HTTPResponse

HOME_ASSISTANT_URL = 'https://virtualmaid.duckdns.org:8123' 
VERIFY_SSL = True  
TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiIzMzcxNTk5YzJjYTU0NmVlYjU0MjM3OGUxYzZkMGNjYSIsImlhdCI6MTY4MDEyNTAyNiwiZXhwIjoxOTk1NDg1MDI2fQ.jSc768Ic_Y4CpQVDpUTpmn7NwDUw3N_uQBYUs6doKTk'  # ADD YOUR LONG LIVED TOKEN IF NEEDED OTHERWISE LEAVE BLANK
DEBUG = False  # SET TO TRUE IF YOU WANT TO SEE MORE DETAILS IN THE LOGS

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

electrodomestic = "Electrodomestico"
hora_barata = 0
ahora = 25


class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool

        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response  
        speak_output = "Buenas, indícame el electrodoméstico que quieras utilizar a lo largo del día."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class ActivaControlHandler (AbstractRequestHandler):
    """Handler for ActivaControl Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("ActivaControl")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        slots = handler_input.request_envelope.request.intent.slots # se utiliza para coger todos los slots, en nuestro caso únicamente hay uno: {electrodomestico}
        URL = "https://tarifaluzhora.es"
        page = requests.get(URL)
        
        sp = BeautifulSoup(page.text, 'html.parser')
        div_interes = sp.find("div", class_="inner_block gauge_low")
        num_interes = div_interes.find("span", class_="main_text")
        hora = num_interes.text
        
        numbers = hora.replace(" ", "").split("-")
        global hora_barata
        hora_barata = int(numbers[0][:-1])

        if electrodomestic in slots:
            electro = slots[electrodomestic].value
            speak_output = "El electrodoméstico que quieres activar es {}, y la hora más barata para activarlo son las {}. ¿Quieres activarlo en la hora mas barata o prefieres hacerlo ahora?".format(electro, hora_barata)
            
        
        else:
            speak_output = "No he entendido el electrodomestico que quieres utilizar"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class YesIntentHandler(AbstractRequestHandler):
    """Handler for Yes Intent."""

    def can_handle(self, handler_input):
        """Check for Yes Intent."""
        return ask_utils.is_intent_name('AMAZON.YesIntent')(handler_input)

    def handle(self, handler_input):
        """Handle Yes Intent."""
        speak_output = "Se activará a la hora mas barata, las {}".format(hora_barata)

        ha_url = "https://virtualmaid.duckdns.org:8123/api/services/input_number/set_value"
        
        headers = {
            'Authorization': 'Bearer {}'.format(TOKEN),
            "Content-Type": "application/json"
        }
        data = {
            "entity_id": "input_number.my_number",
            "value": 18
        }
        
        # Enviar la solicitud de API REST a Home Assistant
        response = requests.post(ha_url, headers=headers, data=json.dumps(data))
        
        
        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class NoIntentHandler(AbstractRequestHandler):
    """Handler for No Intent."""

    def can_handle(self, handler_input):
        """Check for No Intent."""
        return ask_utils.is_intent_name('AMAZON.NoIntent')(handler_input)

    def handle(self, handler_input):
        """Handle No Intent."""
        speak_output = "Se activará ahora"
        
        # logger.debug('Event: %s', event)

        ha_url = "https://virtualmaid.duckdns.org:8123/api/services/input_number/set_value"
        
        headers = {
            'Authorization': 'Bearer {}'.format(TOKEN),
            "Content-Type": "application/json"
        }
        data = {
            "entity_id": "input_number.my_number",
            "value": ahora
        }
        
        # Enviar la solicitud de API REST a Home Assistant
        response = requests.post(ha_url, headers=headers, data=json.dumps(data))

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Indícame el electrodoméstico que quieres activar"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input) or
                ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Adios!"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class FallbackIntentHandler(AbstractRequestHandler):
    """Single handler for Fallback Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In FallbackIntentHandler")
        speech = "Hmm, No te he entendido. Indícame un electrodoméstico."
        reprompt = "I didn't catch that. What can I help you with?"

        return handler_input.response_builder.speak(speech).ask(reprompt).response

class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        # Any cleanup logic goes here.

        return handler_input.response_builder.response


class IntentReflectorHandler(AbstractRequestHandler):
    """The intent reflector is used for interaction model testing and debugging.
    It will simply repeat the intent the user said. You can create custom handlers
    for your intents by defining them above, then also adding them to the request
    handler chain below.
    """
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("IntentRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        intent_name = ask_utils.get_intent_name(handler_input)
        speak_output = "You just triggered " + intent_name + "."

        return (
            handler_input.response_builder
                .speak(speak_output)
                # .ask("add a reprompt if you want to keep the session open for the user to respond")
                .response
        )


class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Generic error handling to capture any syntax or routing errors. If you receive an error
    stating the request handler chain is not found, you have not implemented a handler for
    the intent being invoked or included it in the skill builder below.
    """
    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.error(exception, exc_info=True)

        speak_output = "Perdón, he tenido problemas intentando hacer lo que me has pedido. Prueba otra vez, por favor."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

# The SkillBuilder object acts as the entry point for your skill, routing all request and response
# payloads to the handlers above. Make sure any new handlers or interceptors you've
# defined are included below. The order matters - they're processed top to bottom.


sb = SkillBuilder()

sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(ActivaControlHandler())
sb.add_request_handler(YesIntentHandler())
sb.add_request_handler(NoIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_request_handler(IntentReflectorHandler()) # make sure IntentReflectorHandler is last so it doesn't override your custom intent handlers

sb.add_exception_handler(CatchAllExceptionHandler())

def lambda_handler(event, context):
    return sb.lambda_handler()(event, context)