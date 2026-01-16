#from .feature_producer.featurizer import Featurizer
#from .model_consumer.model_consumer import HMMPredictor
from .feature_producer.api_client import APIClient
from .feature_producer.measurement_parser import flatten_measurements
from .feature_producer.featurizer import Featurizer

from time import time


def main():
    client = APIClient()
    
    end_time = int(time())
    start_time = end_time - 10800
    
    mes = client.get_all_measurements(start=start_time, end=end_time)["responseData"]
    sensors = flatten_measurements(mes)
    
    featurizer = Featurizer()
    feature_vectors = featurizer.extract_features(sensors)
    
    print(feature_vectors)
    
    
if __name__ == "__main__":
    main()