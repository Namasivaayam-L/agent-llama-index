from llama_deploy import (
    deploy_core,
    ControlPlaneConfig,
)
from llama_deploy.message_queues.redis import RedisMessageQueueConfig

async def main():
    await deploy_core(
        control_plane_config=ControlPlaneConfig(host='0.0.0.0'),
        message_queue_config=RedisMessageQueueConfig(),
    )

# import asyncio

# asyncio.run(main())