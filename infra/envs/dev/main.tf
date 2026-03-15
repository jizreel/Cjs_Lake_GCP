terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = "cjs-lake-dev-base"
  region  = "us-central1"
}

module "gcs" {
  source     = "../../modules/gcs"
  project_id = "cjs-lake-dev-base"
  location   = "US"
  bucket_names = [
    "cjs-lake-dev-base",
    "cjs-lake-dev-base-staging",
    "cjs-lake-dev-base-artifacts",
    "cjs-lake-dev-base-logs"
  ]
}

module "bigquery" {
  source     = "../../modules/bigquery"
  project_id = "cjs-lake-dev-base"
  location   = "US"
  datasets = [
    "bronze_dev",
    "silver_dev",
    "gold_dev",
    "monitoring_dev"
  ]
}
