from llama_deploy import (
    deploy_core,
    ControlPlaneConfig,
    SimpleMessageQueueConfig,
)
from llama_deploy.message_queues.redis import RedisMessageQueueConfig

async def deploy_core_systems():
    await deploy_core(
        control_plane_config=ControlPlaneConfig(host='0.0.0.0'),
        message_queue_config=RedisMessageQueueConfig(host='0.0.0.0', port=6379),
    )


import asyncio

asyncio.run(deploy_core_systems())