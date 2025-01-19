from src.server import app

async def start_fastapi_server():
    import uvicorn

    config = uvicorn.Config(app, host="0.0.0.0", port=5000, reload=True)
    server = uvicorn.Server(config)
    await server.serve()


async def main():
    from src.workflows.func_agent import deploy_func_agent_workflow
    from src.core_systems.main import deploy_core_systems

    print("Starting core systems server...")
    core_system_task = asyncio.create_task(deploy_core_systems())

    # Wait until core_systems is up before proceeding
    # await asyncio.sleep(5)  # Simulate waiting for core systems to initialize

    # print("Starting tutor workflow server...")
    # tutor_workflow_task = asyncio.create_task(deploy_func_agent_workflow())

    # Wait until tutor workflow is up before proceeding
    await asyncio.sleep(5)  # Simulate waiting for func agent to initialize

    print("Starting FastAPI server...")
    fastapi_server_task = asyncio.create_task(start_fastapi_server())

    # Run all servers indefinitely
    await asyncio.gather(core_system_task, fastapi_server_task)
    # await asyncio.gather(core_system_task, tutor_workflow_task, fastapi_server_task)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
