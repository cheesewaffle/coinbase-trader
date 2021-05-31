import datetime
import logging
import trader.engine as engine
import azure.functions as func

def main(mytimer: func.TimerRequest) -> None:
    print('Engine Start')
    engine.main()
    print('Engine Finished')
    
    
    utc_timestamp = datetime.datetime.utcnow().replace(
        tzinfo=datetime.timezone.utc).isoformat()

    if mytimer.past_due:
        logging.info('The timer is past due!')

    logging.info('Python timer trigger function ran at %s', utc_timestamp)
