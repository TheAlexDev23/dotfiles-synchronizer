#!/usr/bin/env python

import os
from openai import OpenAI

client = OpenAI(api_key=os.environ.get("OPENAI_KEY"))


def get_commit_message(model="gpt-3.5-turbo") -> str:
    diff = os.popen("git diff --cached").read()

    if diff is None:
        return "No changes"

    return (
        client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "I want you to act as the author of a commit message in git. I'll enter a git diff, and your job is to convert it into a useful commit message. Do not preface the commit with anything, use the present tense, return the full sentence. Write only title, max 72 characters.",
                },
                {"role": "user", "content": diff},
            ],
            temperature=1,
            max_tokens=256,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
        )
        .choices[0]
        .message.content.capitalize()
    )
