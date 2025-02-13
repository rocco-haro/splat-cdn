// client/config.js
CONFIG = {
    "environment": "local", // | "deployed",
    "architecture": "single-tier", // | "two-tier",
    "endpoints": {
        "cdn": {
            "local": {
                "single-tier": "http://localhost:8000/single-tier",
                "two-tier": "http://localhost:8000/two-tier"
            },
            "deployed": {
                "single-tier": "https://d1234.cloudfront.net",
                "two-tier": "https://d5678.cloudfront.net"
            }
        },
        "services" :{
            "local": "http://localhost:8080",
            "deployed": "https://lambda.aws.net"
        }
    }
}