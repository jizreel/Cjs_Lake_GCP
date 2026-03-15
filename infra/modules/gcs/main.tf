variable "project_id" {}
variable "location" {}
variable "bucket_names" {
  type = list(string)
}

resource "google_storage_bucket" "buckets" {
  for_each                    = toset(var.bucket_names)
  name                        = each.value
  location                    = var.location
  project                     = var.project_id
  uniform_bucket_level_access = true
  force_destroy               = true
}
