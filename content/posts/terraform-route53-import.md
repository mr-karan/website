+++
title = "Import existing Route53 records in Terraform"
date = 2020-10-18T08:10:55+05:30
type = "post"
description = "A quick guide on importing Route53 records to Terraform"
in_search_index = true
[taxonomies]
tags = ["DevOps","Terraform","AWS"]
+++

Terraform has a straightforward way of importing existing records (managed outside Terraform) via `terraform import` command. The usage is documented [here](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route53_record) and works well if you have a handful of records to import. However when you work with custom Terraform modules _and_ have a whole bunch of records to be imported, you'd look out ways to **script** the entire workflow. I did this a few weeks back at work and thought to share a solution which works well for my usecase.

### How it works

The task consists of 3 parts:

#### 1. Import all existing records in a hosted zone using `AWS CLI`.

```sh
aws route53 list-resource-record-sets --hosted-zone-id XXX > data/company-tld.json
```

```py
# Loads the zone records in a dict
def load_records(zone_file=ZONE_FILE):
    with open(zone_file) as record_file:
        data = json.load(record_file)
    return data
```

#### 2. Import the record in Terraform state.

To do this, Terraform CLI comes with an `import` command. However for `import` to work, you need to have a resource declaration in your Terraform file already.

From the [official documentation](https://www.terraform.io/docs/import/index.html#currently-state-only):

> Because of this, prior to running terraform import it is necessary to write manually a resource configuration block for the resource, to which the imported object will be mapped.

To overcome this restriction, we will create a `dummy.tf` and programatically write the configuration block for each record.

```py
# Writes the dummy Terraform template which is required
# before `terraform import` runs.
def template_dummy_file(resource_name):
    add_dummy_record = Template(
        """
	resource "aws_route53_record" "$resource_name" {
	# (resource arguments)
	}
	"""
    )
    dummy_file_path = path.join(TERRAFORM_DIR, "dummy.tf")
    with open(dummy_file_path, "a") as f:
        f.write(add_dummy_record.substitute(resource_name=resource_name))
```

AWS Route53 module can import `aws_route53_record` as decsribed [here](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route53_record#import). We will run this command as a subprocess.

```py
# Shells out `terraform import` command in the host OS.
def terraform_import(resource_name, resource_type):
    import_command = f"terraform import aws_route53_record.{resource_name} {ZONE_ID}_{resource_name}_{resource_type}"
    run(import_command, shell=True, check=True)
```

#### 3. (Optional) Move Resources in a Module

In case you are using a Module to manage AWS Route53 resources, you'll need to move the declaration from `resource` to `module` configuration block. This is described more in detail [here](https://www.terraform.io/docs/commands/state/mv.html#example-move-a-resource-into-a-module).

The module declaration/naming would depend on how the module is configured. To demonstrate, the module I use internally requires the name to be of the format `resource_name-resource_type`. To achieve this, you can call `terraform state mv` as a subprocess:

```python
# Shells out `terraform state mv` command in the host OS.
def terraform_move(resource_name, resource_type):
    mv_command = f"terraform state mv aws_route53_record.{resource_name} 'module.{MODULE_NAME}.aws_route53_record.route53_record[\"{resource_name}-{resource_type}\"]'"
    run(mv_command, shell=True, check=True)
```

That's it! Running `terraform plan` should now show you the changes and if you imported every record correctly you should not see any _drift_ from the real world state.

You can view the entire script here:

```python
import json
from os import getenv, path
from string import Template
from subprocess import run
from sys import exit


ZONE_ID = getenv("ZONE_ID")
MODULE_NAME = getenv("MODULE_NAME")
ZONE_FILE = getenv("ZONE_FILE")
TERRAFORM_DIR = getenv("TERRAFORM_DIR")

# Returns the variable key if not present in ENV.
def check_env_vars():
    if not ZONE_FILE:
        return "$ZONE_FILE"
    if not ZONE_ID:
        return "$ZONE_ID"
    if not MODULE_NAME:
        return "$MODULE_NAME"
    if not TERRAFORM_DIR:
        return "$TERRAFORM_DIR"
    return ""


# Loads the zone records in a dict
def load_records(zone_file=ZONE_FILE):
    with open(zone_file) as record_file:
        data = json.load(record_file)
    return data


# Writes the dummy Terraform template which is required
# before `terraform import` runs.
def template_dummy_file(resource_name):
    add_dummy_record = Template(
        """
	resource "aws_route53_record" "$resource_name" {
	# (resource arguments)
	}
	"""
    )
    dummy_file_path = path.join(TERRAFORM_DIR, "dummy.tf")
    with open(dummy_file_path, "a") as f:
        f.write(add_dummy_record.substitute(resource_name=resource_name))


# Shells out `terraform import` command in the host OS.
def terraform_import(resource_name, resource_type):
    import_command = f"terraform import aws_route53_record.{resource_name} {ZONE_ID}_{resource_name}_{resource_type}"
    run(import_command, shell=True, check=True)


# Shells out `terraform state mv` command in the host OS.
def terraform_move(resource_name, resource_type):
    mv_command = f"terraform state mv aws_route53_record.{resource_name} 'module.{MODULE_NAME}.aws_route53_record.route53_record[\"{resource_name}-{resource_type}\"]'"
    run(mv_command, shell=True, check=True)


if __name__ == "__main__":
    missing = check_env_vars()
    if missing:
        exit(f"Required env variable {missing} is missing.")
    records = load_records()
    for i in records.get("ResourceRecordSets"):
        resource_name = i.get("Name")
        resource_type = i.get("Type")
        template_dummy_file(resource_name)
        terraform_import(resource_name, resource_type)
        terraform_move(resource_name, resource_type)
        print(f"Imported {resource_name}")
```

Hope this tiny Python script helps you transition your AWS Route53 records neatly and effortlessly!

Fin!
