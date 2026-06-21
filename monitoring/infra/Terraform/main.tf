terraform {
  required_version = ">= 1.5.0"
  required_providers {
    kubernetes = { source = "hashicorp/kubernetes", version = "~> 2.27" }
  }
}

provider "kubernetes" {
  config_path = var.kubeconfig_path
}

variable "kubeconfig_path" {
  description = "Path to kubeconfig file"
  type        = string
  default     = "~/.kube/config"
}

resource "kubernetes_namespace" "referrals" {
  metadata { name = var.namespace }
}

variable "namespace" {
  description = "Kubernetes namespace"
  type        = string
  default     = "referrals"
}
