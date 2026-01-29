
try:
    from groq import Groq
    import inspect
    
    print(f"Groq imported successfully: {Groq}")
    # Use dummy key just to init client
    client = Groq(api_key="gsk_dummy")
    print(f"Client type: {type(client)}")
    print(f"Client dir: {dir(client)}")
    
    if hasattr(client, 'audio'):
        print("Client has 'audio' attribute")
        print(f"Audio type: {type(client.audio)}")
        print(f"Audio dir: {dir(client.audio)}")
    else:
        print("Client MISSING 'audio' attribute")
        
except Exception as e:
    print(f"Error: {e}")
