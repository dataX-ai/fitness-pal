import requests

def test_webhook():
    url = "http://localhost:8000/webhook/"
    
    # Simulate Twilio POST data
    data = {
        "Body": "hello",
        "From": "+1234567890",
        "NumMedia": "0",
        "MessageSid": "test_message_id"
    }
    
    try:
        # Send POST request
        response = requests.post(url, data=data)
        
        # Print response
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
    except requests.exceptions.ConnectionError:
        print("Error: Make sure Django server is running (python manage.py runserver)")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_webhook() 