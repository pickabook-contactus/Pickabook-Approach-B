import replicate
import os

# Set token from env or hardcode for testing if needed
# os.environ["REPLICATE_API_TOKEN"] = "..." 

def check_schema(model_name):
    try:
        model = replicate.models.get(model_name)
        version = model.latest_version
        print(f"Checking schema for {model_name}...")
        # print(f"Schema: {version.openapi_schema}") 
        # listing inputs
        if 'Input' in version.openapi_schema['components']['schemas']:
             inputs = version.openapi_schema['components']['schemas']['Input']['properties'].keys()
             print(f"Inputs: {list(inputs)}")
        else:
             print("Could not find Input schema")
    except Exception as e:
        print(f"Error checking {model_name}: {e}")

if __name__ == "__main__":
    check_schema("fofr/face-to-many")
    check_schema("lucataco/ip_adapter-face-inpaint")
