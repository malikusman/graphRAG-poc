# Vertex AI Setup Guide

This guide will walk you through setting up Google Cloud Vertex AI to use with SageWrite GraphRAG application.

## Prerequisites

- Google Cloud account with billing enabled (you mentioned having free credits)
- Access to Google Cloud Console

## Step-by-Step Setup

### Step 1: Create or Select a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. If you don't have a project:
   - Click "Select a project" → "New Project"
   - Enter a project name (e.g., "sagewrite-vertexai")
   - Click "Create"
3. If you already have a project, select it from the project dropdown

**Note your Project ID** - you'll need it for the configuration (it's different from the project name).

### Step 2: Enable Vertex AI API

1. In the Google Cloud Console, go to **APIs & Services** → **Library**
   - Direct link: https://console.cloud.google.com/apis/library/aiplatform.googleapis.com
2. Search for "Vertex AI API"
3. Click on "Vertex AI API" from the results
4. Click **"Enable"** button
5. Wait for the API to be enabled (usually takes a few seconds)

### Step 3: Create a Service Account

1. Go to **IAM & Admin** → **Service Accounts**
   - Direct link: https://console.cloud.google.com/iam-admin/serviceaccounts
2. Click **"Create Service Account"**
3. Fill in the details:
   - **Service account name**: `sagewrite-vertexai` (or any name you prefer)
   - **Service account ID**: Will be auto-generated
   - **Description**: "Service account for SageWrite GraphRAG Vertex AI integration"
4. Click **"Create and Continue"**

### Step 4: Grant Permissions

1. In the "Grant this service account access to project" step:
   - Select the role: **"Vertex AI User"** (search for it in the role dropdown)
   - This role provides the necessary permissions to use Vertex AI services
2. Click **"Continue"**
3. Click **"Done"** (you can skip the optional steps)

### Step 5: Create and Download JSON Key

1. Find your newly created service account in the list
2. Click on the service account email address
3. Go to the **"Keys"** tab
4. Click **"Add Key"** → **"Create new key"**
5. Select **"JSON"** as the key type
6. Click **"Create"**
7. The JSON key file will be automatically downloaded to your computer
8. **IMPORTANT**: Keep this file secure! It contains credentials that allow access to your Google Cloud resources.

### Step 6: Configure Environment Variables

You have two options for authentication:

#### Option A: Using GOOGLE_APPLICATION_CREDENTIALS (Recommended)

1. Move the downloaded JSON key file to a secure location (e.g., `~/.credentials/vertexai-key.json`)
2. Set the environment variable:
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-account-key.json"
   ```

#### Option B: Using VERTEX_AI_CREDENTIALS_PATH

1. Add the path to your `.env` file:
   ```bash
   VERTEX_AI_CREDENTIALS_PATH=/path/to/your/service-account-key.json
   ```

### Step 7: Set Up Application Configuration

Add the following to your `.env` file (or set as environment variables):

```bash
# Provider Selection
LLM_PROVIDER=vertexai
EMBEDDING_PROVIDER=vertexai

# Vertex AI Configuration
VERTEX_AI_PROJECT_ID=your-google-cloud-project-id
VERTEX_AI_LOCATION=us-central1
VERTEX_AI_MODEL_ID=gemini-pro
VERTEX_AI_EMBEDDING_MODEL_ID=textembedding-gecko@003
```

**Configuration Details:**
- `VERTEX_AI_PROJECT_ID`: Your Google Cloud Project ID (not the project name)
- `VERTEX_AI_LOCATION`: The region where Vertex AI is available (e.g., `us-central1`, `europe-west4`, `asia-southeast1`)
- `VERTEX_AI_MODEL_ID`: LLM model to use. Options:
  - `gemini-pro` - Standard Gemini Pro model
  - `gemini-1.5-pro` - More capable model
  - `gemini-1.5-flash` - Faster, more cost-effective model
- `VERTEX_AI_EMBEDDING_MODEL_ID`: Embedding model. Options:
  - `textembedding-gecko@003` - 768 dimensions (recommended)
  - `textembedding-gecko-multilingual@001` - For multilingual support

### Step 8: Verify Setup

Run the test script to verify everything is working:

```bash
poetry run python test_vertexai_integration.py
```

This will:
- Check your environment configuration
- Test LLM provider initialization
- Test LLM generation
- Test embedding generation
- Test integration with services

## Troubleshooting

### Error: "Failed to initialize Vertex AI"
- **Check**: Is `GOOGLE_APPLICATION_CREDENTIALS` set correctly?
- **Check**: Does the JSON key file exist at the specified path?
- **Check**: Is the Vertex AI API enabled for your project?

### Error: "Permission denied" or "403 Forbidden"
- **Check**: Does the service account have the "Vertex AI User" role?
- **Check**: Is billing enabled for your Google Cloud project?
- **Check**: Are you using the correct Project ID (not project name)?

### Error: "Model not found" or "404 Not Found"
- **Check**: Is the `VERTEX_AI_MODEL_ID` correct? Check available models in Vertex AI Model Garden
- **Check**: Is the model available in your selected `VERTEX_AI_LOCATION`?

### Error: "Quota exceeded" or "Billing required"
- **Check**: Is billing enabled for your project?
- **Check**: Have you exceeded your free tier limits?
- **Note**: Vertex AI requires billing to be enabled, even for free tier usage

## Testing with Your Application

Once setup is complete, you can test the integration:

1. **Test LLM Generation:**
   ```python
   from app.core.llm_provider import get_llm
   from langchain_core.messages import HumanMessage
   
   llm = get_llm(temperature=0.1)
   response = await llm.ainvoke([HumanMessage(content="Hello!")])
   print(response.content)
   ```

2. **Test Embeddings:**
   ```python
   from app.core.embedding_provider import get_embedding_provider
   
   provider = get_embedding_provider()
   embedding = provider.generate_embedding("Test text")
   print(f"Embedding dimensions: {len(embedding)}")
   ```

3. **Run Full GraphRAG Pipeline:**
   - Use your existing pipeline test scripts
   - Make sure `LLM_PROVIDER=vertexai` and `EMBEDDING_PROVIDER=vertexai` are set

## Additional Resources

- [Vertex AI Documentation](https://cloud.google.com/vertex-ai/docs)
- [Vertex AI Pricing](https://cloud.google.com/vertex-ai/pricing)
- [Gemini Model Guide](https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/gemini)
- [Embedding Models Guide](https://cloud.google.com/vertex-ai/generative-ai/docs/embeddings/get-text-embeddings)

## Cost Considerations

- **Free Tier**: Google Cloud provides $300 in free credits for new accounts
- **Gemini Models**: Pricing varies by model (check current pricing in Google Cloud Console)
- **Embeddings**: `textembedding-gecko@003` is generally cost-effective
- **Monitoring**: Monitor usage in Google Cloud Console → Vertex AI → Usage & Quotas

## Security Best Practices

1. **Never commit your service account JSON key to version control**
2. **Use environment variables** or secure secret management
3. **Rotate keys periodically** for security
4. **Limit service account permissions** to only what's needed (Vertex AI User role)
5. **Use different service accounts** for development and production




