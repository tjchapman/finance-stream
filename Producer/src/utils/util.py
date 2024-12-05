import finnhub

def create_client(token:str):
    return finnhub.Client(api_key=token)

