from projen.awscdk import AwsCdkPythonApp
from projen.python import VenvOptions
from projen.vscode import (
    VsCode,
    VsCodeLaunchConfig,
    VsCodeSettings,
)
from projen import (
    Project,
    Makefile,
    TextFile,
)

VENV_DIR = ".venv"
project: Project = AwsCdkPythonApp(
    author_email="jacobpetterle+aiforu@gmail.com",
    author_name="Jacob Petterle",
    cdk_version="2.1.0",
    module_name="taisearch",
    name="tai-search-service",
    version="0.1.0",
    venv_options=VenvOptions(envdir=VENV_DIR),
    deps=[
        "pydantic<=1.10.11",
        "loguru",
        "boto3",
        "requests",
        "pymongo",
        "pygit2",
        "fastapi<=0.98.0",
        "pydantic[dotenv]<=1.10.11",
        "aws-lambda-powertools",
        "pytest",
        "pytest-cov",
        "uvicorn",
        "pinecone-client[grpc]",
        "langchain==0.0.229",
        "pymongo",
        "filetype",
        "beautifulsoup4",
        "openai",
        "tiktoken",
        "aws-lambda-powertools",
        "pinecone-text",
        "pinecone-text[splade]",
        "pymupdf",
        "pdf2image",
        "PyPDF2",
        "unstructured",
        "selenium",
    ],
    dev_deps=[
        "boto3-stubs[secretsmanager]",
        "boto3-stubs[essential]",
        "aws-lambda-typing",
        "boto3-stubs[essential]",
        "ipykernel",
    ],
)

env_file: TextFile = TextFile(
    project,
    "./.env",
    lines=[
        'PINECONE_DB_API_KEY_SECRET_NAME="dev/tai_service/pinecone_db/api_key"',
        'OPENAI_API_KEY_SECRET_NAME="dev/tai_service/openai/api_key"',
        'PINECONE_DB_ENVIRONMENT="us-east-1-aws"',
        'DOC_DB_READ_ONLY_USER_PASSWORD_SECRET_NAME="dev/tai_service/document_DB/read_ONLY_user_password"',
        'DOC_DB_READ_WRITE_USER_PASSWORD_SECRET_NAME="dev/tai_service/document_DB/read_write_user_password"',
        'DOC_DB_ADMIN_USER_PASSWORD_SECRET_NAME="dev/tai_service/document_DB/admin_password"',
        'AWS_DEPLOYMENT_ACCOUNT_ID="645860363137"',
        'DEPLOYMENT_TYPE="dev"',
    ]
)
make_file: Makefile = Makefile(
    project,
    "./makefile",
)
make_file.add_rule(
    targets=["deploy-all"],
    recipe=[
        "cdk deploy --all --require-approval never",
    ],
)
make_file.add_rule(
    targets=["unit-test"],
    recipe=[
        "python3 -m pytest -vv tests/unit --cov=taiservice --cov-report=term-missing --cov-report=xml:test-reports/coverage.xml --cov-report=html:test-reports/coverage",
    ]
)
make_file.add_rule(
    targets=["functional-test"],
    recipe=[
        "python3 -m pytest -vv tests/functional --cov=taiservice --cov-report=term-missing --cov-report=xml:test-reports/coverage.xml --cov-report=html:test-reports/coverage",
    ]
)
make_file.add_rule(
    targets=["full-test"],
    prerequisites=["unit-test", "functional-test"],
)
make_file.add_rule(
    targets=["test-deploy-all"],
    prerequisites=["full-test", "deploy-all"],
)
make_file.add_rule(
    targets=["start-docker"],
    recipe=[
        "sudo systemctl start docker",
    ],
)
def convert_dict_env_vars_to_docker_env_vars(env_vars: dict):
    return " ".join([f"-e {key}=\"{value}\"" for key, value in env_vars.items()])

RUNTIME_ENV_VARS = {
    "PINECONE_DB_API_KEY_SECRET_NAME": "dev/tai_service/pinecone_db/api_key",
    "PINECONE_DB_ENVIRONMENT": "us-east-1-aws",
    "PINECONE_DB_INDEX_NAME": "tai-index",
    "DOC_DB_CREDENTIALS_SECRET_NAME": "dev/tai_service/document_DB/read_write_user_password",
    "DOC_DB_USERNAME_SECRET_KEY": "username",
    "DOC_DB_PASSWORD_SECRET_KEY": "password",
    "DOC_DB_FULLY_QUALIFIED_DOMAIN_NAME": "tai-service-645860363137.us-east-1.docdb-elastic.amazonaws.com",
    "DOC_DB_PORT": "27017",
    "DOC_DB_DATABASE_NAME": "class_resources",
    "DOC_DB_CLASS_RESOURCE_COLLECTION_NAME": "class_resource",
    "DOC_DB_CLASS_RESOURCE_CHUNK_COLLECTION_NAME": "class_resource_chunk",
    "OPENAI_API_KEY_SECRET_NAME": "dev/tai_service/openai/api_key",
    "AWS_DEFAULT_REGION": "us-east-1",
    "COLD_STORE_BUCKET_NAME": "tai-service-class-resource-cold-store-dev",
    "NLTK_DATA": "/tmp/nltk_data",
}
make_file.add_rule(
    targets=["build-and-run-docker"],
    recipe=[
        "cdk synth && \\",
        "cd $(DIR) && \\",
        "docker build -t test-container . && \\",
        f"docker run --network host {convert_dict_env_vars_to_docker_env_vars(RUNTIME_ENV_VARS)} test-container",
    ],
)
make_file.add_rule(
    targets=["test-docker-lambda"],
    recipe=[
        'curl localhost:8000/',
    ],
)
make_file.add_rule(
    targets=["docker-clean-all-force"],
    recipe=[
        "docker system prune --all --force",
    ],
)
vscode = VsCode(project)
vscode_launch_config: VsCodeLaunchConfig = VsCodeLaunchConfig(vscode)
vscode_launch_config.add_configuration(
    name="TAI Search Service",
    type="python",
    request="launch",
    program="${workspaceFolder}/.venv/bin/uvicorn",
    args=[
        "taiservice.searchservice.main",
        "--reload",
        "--factory",
    ],
    env=RUNTIME_ENV_VARS,
)

vscode_settings: VsCodeSettings = VsCodeSettings(vscode)
vscode_settings.add_setting("python.formatting.provider", "none")
vscode_settings.add_setting("python.testing.pytestEnabled", True)
vscode_settings.add_setting("python.testing.pytestArgs", ["tests"])
vscode_settings.add_setting("editor.formatOnSave", True)

project.add_git_ignore(".build*")

project.synth()