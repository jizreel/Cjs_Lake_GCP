variable "project_id" {}
variable "location" {}
variable "datasets" {
  type = list(string)
}

resource "google_bigquery_dataset" "datasets" {
  for_each   = toset(var.datasets)
  project    = var.project_id
  dataset_id = each.value
  location   = var.location
}
