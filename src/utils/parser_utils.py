import re


def clean_llm_json(content):

    if isinstance(content, list):

        content = "\n".join(
            str(x)
            for x in content
        )

    content = content.strip()

    content = re.sub(
        r"^```json",
        "",
        content,
        flags=re.IGNORECASE
    )

    content = re.sub(
        r"^```",
        "",
        content
    )

    content = re.sub(
        r"```$",
        "",
        content
    )

    return content.strip()