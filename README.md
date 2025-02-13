# splat-cdn
Experimental study comparing tiered caching &amp; HTTP protocols for proximity-based content delivery.
We aim to test the diff in performance (latency) between:
* a one or two tiered cache system
* http 2 versus http 3. 

We define a set of services that help conduct real-world simulations i.e. a user traversing a digital landscape and requesting splats on-the-fly. A client follows a pre-defined path with predictable asset requests. The path and assets are generated through a script to assist in creating different scenarios i.e. a garden variety of options including but not limited to: 
1) splat size distribution
2) splat request per position change
3) path taken

The mock cdn exists to help local development and fine tune experiment data before deploying to a live CDN.

We'll deploy to AWS lambda, cloudfront, and S3 using Terraform scripts and the aws cli. 

## Completed:
* valid path and data generation
* lambda services to receive paths
* mock cdn with http 1.1,2 and 3 support 
* functional client that runs simulations 

## TODO:
* Tune the data generation to support experiments to prove the null hypothesis 
* Clean up the client to make it easier to run experiments w/o refreshing
* Update services to preload assets to the spawn point
* Update services to support predicting the next set of assets
* Run experiments locally and draw conclusions
* Deploy the data to S3, services to lambda, and setup cloud front
* Run experiments in the deployed environment and draw conclusions

# Project Structure
```
/prototype/
├── mock-data-generator/  # Experiment data generation
├── lambda-service/       # API service code
├── client/               # Infrastructure setup
├── cdn/                  # mock cdn for local development
└── README.md             # This file
```

## Experiment Workflow

### 1. Generate Mock Data
visit mock-data-generator/README.md

### 2. Deploy Infrastructure 
WIP
### 3. Upload Experiment Data
WIP
### 4. Update Lambda Config (if needed)

## Local Development

When developing locally:
1. Mock data is generated in the local filesystem
2. The mock CDN service simulates both single-tier and two-tier setups
3. Lambda service can be run locally using SAM CLI or similar tools
