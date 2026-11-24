import asyncio

from app.services.interview_graph import run_interview_graph


async def main():

    result = await run_interview_graph(
        candidate_answer="React uses components to build interfaces.",
        role="React Developer"
    )

    print("\nGRAPH RESULT:")
    print(result)


asyncio.run(main())