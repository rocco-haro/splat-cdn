import json
import boto3
import os
from typing import Dict, List
import math

# Initialize AWS clients
cloudfront = boto3.client('cloudfront')
s3 = boto3.client('s3')

# Get environment variables
BUCKET_NAME = os.environ['S3_BUCKET']
SINGLE_TIER_DISTRIBUTION_ID = os.environ['SINGLE_TIER_DISTRIBUTION_ID']
TWO_TIER_DISTRIBUTION_ID = os.environ['TWO_TIER_DISTRIBUTION_ID']

def predict_future_position(position: Dict, velocity: Dict, time_delta: float) -> Dict:
    """
    Predict future position based on current position and velocity
    """
    return {
        "x": position["x"] + velocity["x"] * time_delta,
        "y": position["y"] + velocity["y"] * time_delta,
        "z": position["z"] + velocity["z"] * time_delta
    }

def get_splats_in_range(position: Dict, radius: float) -> List[str]:
    """
    Get list of splat IDs within radius of position
    """
    # Convert position to grid coordinates
    grid_x = math.floor(position["x"] / 5.0)  # Assuming 5.0 is grid cell size
    grid_y = math.floor(position["y"] / 5.0)
    grid_z = math.floor(position["z"] / 5.0)
    
    # Get surrounding grid cells based on radius
    radius_cells = math.ceil(radius / 5.0)
    splats = []
    
    for x in range(grid_x - radius_cells, grid_x + radius_cells + 1):
        for y in range(grid_y - radius_cells, grid_y + radius_cells + 1):
            for z in range(grid_z - radius_cells, grid_z + radius_cells + 1):
                splat_id = f"{x}_{y}_{z}"
                # Check if splat exists in S3
                try:
                    s3.head_object(Bucket=BUCKET_NAME, Key=f"splats/{splat_id}.splat")
                    splats.append(splat_id)
                except:
                    continue
    
    return splats

def trigger_preload(splat_ids: List[str], distribution_id: str):
    """
    Trigger CloudFront preload for splats
    """
    paths = [f"/splats/{splat_id}.splat" for splat_id in splat_ids]
    
    try:
        # Create invalidation to force refresh from origin
        cloudfront.create_invalidation(
            DistributionId=distribution_id,
            InvalidationBatch={
                'Paths': {
                    'Quantity': len(paths),
                    'Items': paths
                },
                'CallerReference': str(time.time())
            }
        )
    except Exception as e:
        print(f"Error triggering preload: {str(e)}")

def handler(event, context):
    """
    Process location updates from SQS
    """
    try:
        for record in event['Records']:
            # Parse message
            message = json.loads(record['body'])
            position = message['position']
            velocity = message['velocity']
            
            # Predict positions for next 5 seconds
            predicted_positions = []
            for t in range(5):
                predicted_positions.append(
                    predict_future_position(position, velocity, t + 1)
                )
            
            # Get splats for current and predicted positions
            splats_to_preload = set()
            
            # Current position - smaller radius
            current_splats = get_splats_in_range(position, 5.0)
            splats_to_preload.update(current_splats)
            
            # Predicted positions - larger radius
            for pos in predicted_positions:
                future_splats = get_splats_in_range(pos, 10.0)
                splats_to_preload.update(future_splats)
            
            # Trigger preload for both distribution types
            trigger_preload(list(splats_to_preload), SINGLE_TIER_DISTRIBUTION_ID)
            trigger_preload(list(splats_to_preload), TWO_TIER_DISTRIBUTION_ID)
        
        return {
            "statusCode": 200,
            "body": json.dumps({"status": "success"})
        }
        
    except Exception as e:
        print(f"Error processing location updates: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }