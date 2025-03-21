import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from src.embeddings import map_texts_cosine_with_cache

category_descriptions = {
    "ci_cd": "CI/CD pipelines for automated build, test, and deployment using GitHub Actions, Jenkins, or GitLab CI.",
    "iac": "Infrastructure as code for provisioning resources using Terraform, CloudFormation, or Ansible.",
    "config": "Configuration files with environment variables, service endpoints, and application settings."
}

def report(project):
    chunks = split_readme_to_chunks(project.doc_path)
    report = ""
    for witem in project.walk_items:
        root = witem.root
        files = witem.files
        for file in files:
            file_path = os.path.join(root, file)
            cat = classify_file(file_path)
            if cat:
                im = is_mentioned(category_descriptions[cat], chunks)
                if not im:
                    report += f"File {file_path} points on {cat.upper()} in your project. But it doesn't seem to be documented\n"
    print(report)

def is_mentioned(description, chunks):
    res = map_texts_cosine_with_cache([description], chunks)
    for d in res:
        for c in d:
            if c > 0.6:
                return True
    return False


def split_readme_to_chunks(doc_path, chunk_size=500, chunk_overlap=50):
    with open(doc_path, "r", encoding="utf-8") as f:
        readme_text = f.read()
    splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        separators=["\n### ", "\n## ", "\n# ", "\n\n", "\n", " "],
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    chunks = splitter.split_text(readme_text)
    return chunks


def classify_file(file_path):
    file_name = os.path.basename(file_path).lower()
    path_lower = file_path.lower()

    # CI/CD patterns
    ci_cd_keywords = ["github/workflows", ".gitlab-ci", "circleci", "azure-pipelines", "jenkinsfile", "travis.yml", ".drone.yml"]
    ci_cd_files = ["ci.yml", "ci.yaml", "build.yml", "build.yaml", "pipeline.yml", "pipeline.yaml"]

    # IaC patterns
    iac_extensions = [".tf", ".tf.json", ".tfvars", ".yaml", ".yml"]
    iac_keywords = ["terraform", "cloudformation", "cdk", "ansible", "pulumi", "infrastructure", "iac"]

    # Config patterns
    config_files = [
        "config.json", "config.yaml", "config.yml", "settings.json", "settings.yaml", "settings.yml",
        "application.yml", "application.yaml", ".env", "env.yaml", "env.yml"
    ]
    config_extensions = [".env", ".ini", ".conf"]

    # CI/CD detection
    if any(kw in path_lower for kw in ci_cd_keywords) or file_name in ci_cd_files or "ci" in file_name:
        return "ci_cd"

    # IaC detection
    if any(kw in path_lower for kw in iac_keywords) or os.path.splitext(file_name)[1] in iac_extensions:
        return "iac"

    # Config detection
    if file_name in config_files or os.path.splitext(file_name)[1] in config_extensions:
        return "config"

    return None
