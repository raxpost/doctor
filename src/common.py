import os
from src.exclusions import is_file_to_skip
from tqdm import tqdm
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.text_splitter import CharacterTextSplitter
from src.embeddings import map_texts_cosine_with_cache

categories = {
    "CI/CD": {
        "description": "Continuous integration, Continuous delivery, CI/CD pipelines for automated build, test, and deployment using GitHub Actions, Jenkins, or GitLab CI.",
        "files_patterns":  ["github/workflows", ".gitlab-ci", "circleci", "azure-pipelines", "jenkinsfile", "travis.yml", ".drone.yml", "ci.yml", "ci.yaml", "build.yml", "build.yaml", "pipeline.yml", "pipeline.yaml", "serverless.yml"],
    },
    "Infrastructure as Code": {
        "description": "infrastructure, IaC, iac, Infrastructure as code for provisioning resources using Terraform, CloudFormation, or Ansible, infrastructure",
        "files_patterns": [".tf", ".tf.json", ".tfvars", "terraform", "cloudformation", "cdk", "ansible", "pulumi", "infrastructure", "iac"]
    },
    "Configuration": {
        "description": "Configuration files with environment variables, service endpoints, and application settings.",
        "files_patterns": ["config.json", "config.yaml", "config.yml", "settings.json", "settings.yaml", "settings.yml",
        "application.yml", "application.yaml", "env.yaml", "env.yml", ".env", ".ini", ".conf"]
    },
    "Installation process": {
        "description": "Installation, install instructions, setup steps, dependencies, system requirements",
        "files_patterns": [
            # Generic / multi-language
            "Makefile", "install.sh", "bootstrap.sh", "build.sh", "install.bat",
            "configure", "/configure", "CMakeLists.txt",

            # Python
            "setup.py", "setup.cfg", "pyproject.toml", "requirements.txt", "Pipfile", "Pipfile.lock", "environment.yml",

            # JavaScript / TypeScript
            "package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "tsconfig.json", "vite.config.js", "webpack.config.js",

            # Java
            "pom.xml", "build.gradle", "build.gradle.kts", "settings.gradle", "settings.gradle.kts", "gradlew", "gradlew.bat", "mvnw", "mvnw.cmd",

            # Go
            "go.mod", "go.sum", "main.go",

            # C++
            "CMakeLists.txt", "*.vcxproj", "*.sln", "conanfile.txt", "conanfile.py", "vcpkg.json",

            # Rust
            "Cargo.toml", "Cargo.lock",

            # Swift
            "Package.swift", "Cartfile", "Cartfile.resolved", "Podfile", "Podfile.lock",

            # PHP
            "composer.json", "composer.lock",

            # Common docs
            "INSTALL.md", "install.md", "install.rst", "README.md", "readme.md"
        ]
    },
    "Deployment process": {
        "description": "Scripts and configuration files used to deploy the application to staging or production environments, including cloud deployment, containers, package publishing, and artifact delivery.",
        "files_patterns": [
            "deploy.sh",
            "deployment.sh",
            "kubernetes.yaml",
            "k8s.yaml",
            "k8s.yml",
            "helmfile.yaml",
            "helmfile.yml",
            "Chart.yaml",
            "values.yaml",
            "docker-compose.yml",
            "docker-compose.yaml",
            "Dockerfile",
            "Procfile",
            "app.yaml",                    # e.g. for Google App Engine
            ".ebextensions",              # AWS Elastic Beanstalk
            "ecs-params.yml",             # AWS ECS
            ".elasticbeanstalk",          # AWS EB config dir
            ".platform.app.yaml",         # Platform.sh
            "now.json",                   # Vercel
            "vercel.json",
            "netlify.toml",
            "fly.toml",
            "render.yaml",
            "cloudbuild.yaml",            # Google Cloud Build
            "azure-pipelines.yml"
        ]
    }
}

def report(project):
    chunks = split_readme_to_chunks(project.doc_path)
    report = ""
    filtered_files = []
    for witem in project.walk_items:
        root = witem.root
        files = witem.files
        for file in files:
            file_path = os.path.join(root, file)
            if is_file_to_skip(file_path):
                continue
            cat = classify_file(file_path)
            if cat:
                filtered_files.append((file_path, cat))

    for pr in tqdm(filtered_files):
        file_path = pr[0]
        cat = pr[1]
        im = is_mentioned(categories[cat]["description"], chunks)
        if not im:
            report += f"File {file_path} points on {cat.upper()} in your project. But it doesn't seem to be documented\n"
    print(report)

def is_mentioned(description, chunks):
    res = map_texts_cosine_with_cache([description], chunks)
    for d in res:
        for i, c in enumerate(d):
            if c > 0.6:
                return True
    return False


def split_readme_to_chunks(doc_path, chunk_size=500, chunk_overlap=50):
    with open(doc_path, "r", encoding="utf-8") as f:
        readme_text = f.read()
    splitter = RecursiveCharacterTextSplitter(
        separators=["\n### ", "\n## ", "\n# ", "\n\n", "\n", " "],
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    chunks = splitter.split_text(readme_text)
    return chunks


def classify_file(file_path):
    path_lower = file_path.lower()

    for key, item in categories.items():
        fpats = item["files_patterns"]
        if any(kw in path_lower for kw in fpats):
            return key

    return None
