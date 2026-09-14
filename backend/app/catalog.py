from app.models import Image, InstanceType

INSTANCE_TYPES = [
    InstanceType(
        id="1x-a100",
        gpu_model="A100 80GB",
        gpu_count=1,
        vcpus=22,
        memory_gb=120,
        price_per_hour=1.29,
    ),
    InstanceType(
        id="1x-h100",
        gpu_model="H100 80GB",
        gpu_count=1,
        vcpus=22,
        memory_gb=185,
        price_per_hour=2.29,
    ),
    InstanceType(
        id="2x-h100",
        gpu_model="H100 80GB",
        gpu_count=2,
        vcpus=44,
        memory_gb=370,
        price_per_hour=4.58,
    ),
    InstanceType(
        id="8x-h100",
        gpu_model="H100 80GB",
        gpu_count=8,
        vcpus=176,
        memory_gb=1480,
        price_per_hour=18.32,
    ),
]

IMAGES = [
    Image(id="ubuntu-24.04-cuda-12.8", name="Ubuntu 24.04 + CUDA 12.8"),
    Image(id="ubuntu-22.04-cuda-12.4", name="Ubuntu 22.04 + CUDA 12.4"),
    Image(id="pytorch-2.8-cuda-12.8", name="PyTorch 2.8 (Ubuntu 24.04, CUDA 12.8)"),
]

INSTANCE_TYPES_BY_ID = {instance_type.id: instance_type for instance_type in INSTANCE_TYPES}
IMAGES_BY_ID = {image.id: image for image in IMAGES}
