# GPU Console

A self-service console where a single team launches, inspects and deletes GPU Instances, each of which becomes reachable by name on a private network. Instances are never stopped and started; they are only launched and deleted.

## Language

### Instances

**Instance**:
A GPU machine a user has launched, from the moment it is launched until its deletion finishes.
_Avoid_: VM, server, machine, node

**Name**:
The user-chosen label that identifies an Instance and forms its Hostname; no two existing Instances share a Name.
_Avoid_: Label, title

**Launch**:
The user action that brings a new Instance into existence from an Instance Type and an Image.
_Avoid_: Create, provision (as a verb), spin up

**Delete**:
The user action that removes an Instance permanently; nothing remains once it finishes, and its Name becomes available again.
_Avoid_: Terminate, destroy, deprovision

### Lifecycle

**Provisioning**:
The phase after Launch while the Instance is being brought up and cannot yet be used.

**Running**:
The phase in which the Instance is up, has an IP Address and is resolvable by Hostname.
_Avoid_: Active, ready, up

**Deleting**:
The phase after Delete while the Instance is being torn down; it is no longer resolvable.

**Failed**:
The phase of an Instance that needs attention because Launch or Delete did not complete; the only thing a user can do with it is Delete it.
_Avoid_: Error, broken

**Failure Reason**:
A short, user-readable explanation of why an Instance's Launch or Delete did not complete; only a Failed Instance has one.
_Avoid_: Error message, cause

### Catalog

**Instance Type**:
A fixed hardware shape an Instance can be launched with: GPU model and count, vCPUs, memory and hourly price.
_Avoid_: Flavor, size, SKU, plan

**Image**:
The operating system and software stack an Instance boots with.
_Avoid_: OS, template, AMI

### Networking

**Instance Network**:
The private address range from which each Instance reserves its IP Address at Launch; when no address is free, Launch is refused.
_Avoid_: Subnet, VPC

**IP Address**:
The address in the Instance Network an Instance holds from Launch until its deletion finishes, in every phase including Failed.

**DNS Zone**:
The domain under which every Instance's Hostname lives.
_Avoid_: Domain, suffix

**Hostname**:
An Instance's Name joined to the DNS Zone.
_Avoid_: FQDN, address, URL

**DNS Record**:
The published mapping from a Running Instance's Hostname to its IP Address; only Running Instances have one.
