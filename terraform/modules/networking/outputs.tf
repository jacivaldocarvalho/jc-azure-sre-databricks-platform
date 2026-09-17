output "vnet_id" {
  description = "ID of the VNet"
  value       = azurerm_virtual_network.main.id
}

output "vnet_name" {
  description = "Name of the VNet"
  value       = azurerm_virtual_network.main.name
}

output "subnet_ids" {
  description = "IDs of all subnets"
  value = {
    for key, subnet in azurerm_subnet.subnets : key => subnet.id
  }
}

output "subnet_names" {
  description = "Names of all subnets"
  value = {
    for key, subnet in azurerm_subnet.subnets : key => subnet.name
  }
}

output "nsg_id" {
  description = "ID of the Network Security Group"
  value       = azurerm_network_security_group.main.id
}

output "nsg_association_ids" {
  description = "IDs of NSG associations per subnet"
  value = {
    for key, assoc in azurerm_subnet_network_security_group_association.associations : key => assoc.id
  }
}