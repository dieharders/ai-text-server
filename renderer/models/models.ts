export enum ModelType {
  Llama = 'llama',
  Mpt = 'mpt',
  GptJ = 'gptj',
  NeoX = 'gptneox',
  Bloom = 'bloom',
  Gpt2 = 'gpt2',
}

export enum LicenseType {
  Commercial = 'Commercial',
  NonCommercial = 'Non-commercial',
  Academic = 'Academic',
  OpenSource = 'Open-source',
  BigScience = 'BigScience RAIL License v1.0',
  MIT = 'MIT',
  Apache2 = 'Apache-2.0',
  GPL = 'GPL',
  Llama2 = 'llama2',
  Other = 'Other',
}

export enum Providers {
  TheBloke = 'The Bloke',
  Together = 'Together',
}

export type ModelIntegrity = {
  sha256: string
}

export interface IModelCard {
  id: string
  name: string
  provider: string
  licenses: Array<string>
  description: string
  fileSize: number
  sha256?: string
  ramSize?: number
  fileName: string
  downloadUrl: string
  modelUrl?: string
  modelType?: string
  promptTemplate?: string
  tokenizers?: string[]
  tags?: string[]
  quantTypes?: string[]
}

export const toGB = (size: number) => {
  return size / 1024 / 1024 / 1024
}

const models: Array<IModelCard> = [
  {
    id: 'llama-2-13b-ensemble',
    name: 'Llama 2 13B Ensemble',
    provider: Providers.TheBloke,
    licenses: [LicenseType.Llama2],
    description:
      'Llama 2 is a collection of pretrained and fine-tuned generative text models ranging in scale from 7 billion to 70 billion parameters. Our fine-tuned LLMs, called Llama-2-Chat, are optimized for dialogue use cases. Llama-2-Chat models outperform open-source chat models on most benchmarks we tested, and in our human evaluations for helpfulness and safety, are on par with some popular closed-source models like ChatGPT and PaLM',
    fileSize: 7.87,
    fileName: 'llama-2-13b-ensemble-v6.Q4_K_M.gguf',
    modelType: ModelType.Llama,
    modelUrl: 'https://huggingface.co/TheBloke/Llama-2-13B-Ensemble-v6-GGUF',
    quantTypes: ['Q5_K_S', 'Q4_K_M', 'Q3_K_S'], // Large, medium, small
    downloadUrl:
      'https://huggingface.co/TheBloke/Llama-2-13B-Ensemble-v6-GGUF/resolve/main/llama-2-13b-ensemble-v6.Q4_K_M.gguf',
    sha256: '90b27795b2e319a93cc7c3b1a928eefedf7bd6acd3ecdbd006805f7a098ce79d', // Q4_K_M
  },
  {
    id: 'llama-2-13b-chat',
    name: 'Llama 2 13B Chat',
    provider: Providers.TheBloke,
    licenses: [LicenseType.Llama2],
    description:
      'Llama 2 is a collection of pretrained and fine-tuned generative text models ranging in scale from 7 billion to 70 billion parameters. Our fine-tuned LLMs, called Llama-2-Chat, are optimized for dialogue use cases. Llama-2-Chat models outperform open-source chat models on most benchmarks we tested, and in our human evaluations for helpfulness and safety, are on par with some popular closed-source models like ChatGPT and PaLM',
    fileSize: 7.87,
    fileName: 'llama-2-13b-chat.Q4_K_M.gguf',
    modelType: ModelType.Llama,
    modelUrl: 'https://huggingface.co/TheBloke/Llama-2-13B-chat-GGUF',
    quantTypes: ['Q5_K_S', 'Q4_K_M', 'Q3_K_S'], // Large, medium, small
    downloadUrl:
      'https://huggingface.co/TheBloke/Llama-2-13B-chat-GGUF/resolve/main/llama-2-13b-chat.Q4_K_M.gguf',
    sha256: '7ddfe27f61bf994542c22aca213c46ecbd8a624cca74abff02a7b5a8c18f787f', // Q4_K_M
  },
  {
    id: 'mistral-7b',
    name: 'Mistral-7B',
    provider: Providers.TheBloke,
    licenses: [LicenseType.Apache2],
    description: 'Mistral Ai',
    fileSize: 4.37,
    fileName: 'mistral-7b-v0.1.Q4_K_M.gguf',
    modelType: ModelType.Llama,
    modelUrl: 'https://huggingface.co/TheBloke/Mistral-7B-v0.1-GGUF',
    quantTypes: ['Q5_K_S', 'Q4_K_M', 'Q3_K_S'], // Large, medium, small
    downloadUrl:
      'https://huggingface.co/TheBloke/Mistral-7B-v0.1-GGUF/resolve/main/mistral-7b-v0.1.Q4_K_M.gguf',
    sha256: 'ce6253d2e91adea0c35924b38411b0434fa18fcb90c52980ce68187dbcbbe40c', // Q4_K_M
  },
  {
    id: 'wizard-coder-python-13b',
    name: 'WizardCoder Python 13B',
    provider: Providers.TheBloke,
    licenses: [LicenseType.Llama2],
    description:
      'Wizardlm: Empowering large language models to follow complex instructions. A StarCoder fine-tuned model using Evol-Instruct method specifically for coding tasks. Use this for code generation, also good at logical reasoning skills.',
    fileSize: 7.87,
    ramSize: 8,
    fileName: 'wizardcoder-python-13b-v1.0.Q4_K_M.gguf',
    modelType: ModelType.Llama,
    modelUrl: 'https://huggingface.co/TheBloke/WizardCoder-Python-13B-V1.0-GGUF',
    downloadUrl:
      'https://huggingface.co/TheBloke/WizardCoder-Python-13B-V1.0-GGUF/resolve/main/wizardcoder-python-13b-v1.0.Q4_K_M.gguf',
    sha256: '50ff7a6a33357a063e0d09b6d43d95dbf62dda5450138541478e524e06a4fe2a',
  },
  {
    id: 'wizard-vicuna-13b-uncensored',
    name: 'Wizard Vicuna 13B Uncensored',
    provider: Providers.TheBloke,
    licenses: [LicenseType.Other],
    description: 'Wizard Vicuna uncensored chat.',
    fileSize: 7.87,
    fileName: 'Wizard-Vicuna-13B-Uncensored.Q4_K_M.gguf',
    modelType: ModelType.Llama,
    modelUrl: 'https://huggingface.co/TheBloke/Mistral-7B-v0.1-GGUF',
    quantTypes: ['Q5_K_S', 'Q4_K_M', 'Q3_K_S'], // Large, medium, small
    downloadUrl:
      'https://huggingface.co/TheBloke/Wizard-Vicuna-13B-Uncensored-GGUF/resolve/main/Wizard-Vicuna-13B-Uncensored.Q4_K_M.gguf',
    sha256: 'e5ca843fd4a8c0a898b036f5c664a1fac366fb278f20880f1a750f38a950db73', // Q4_K_M
  },
  {
    id: 'orca-mini-7b',
    name: 'Orca Mini 7B',
    provider: Providers.TheBloke,
    licenses: [LicenseType.Other],
    description:
      'An Uncensored LLaMA-7b model trained on explain tuned datasets, created using Instructions and Input from WizardLM, Alpaca & Dolly-V2 datasets and applying Orca Research Paper dataset construction approaches.',
    fileSize: 4.08,
    ramSize: 16,
    fileName: 'orca_mini_v3_7b.Q4_K_M.gguf',
    modelType: ModelType.Llama,
    modelUrl: 'https://huggingface.co/TheBloke/orca_mini_v3_7B-GGUF',
    downloadUrl:
      'https://huggingface.co/TheBloke/orca_mini_v3_7B-GGUF/resolve/main/orca_mini_v3_7b.Q4_K_M.gguf',
    sha256: '77ea8409d75f2d5fd125afc346d5059a2411e8996a4e998a3643c945330d7baf',
  },
  {
    id: 'falcon-7b',
    name: 'Falcon 7B',
    provider: Providers.TheBloke, // NikolayKozloff
    licenses: [LicenseType.Other],
    description: 'Quantized version of tiia Falcon model.',
    fileSize: 4.06,
    fileName: 'falcon-7b-Q4_0-GGUF.gguf',
    modelType: ModelType.Llama,
    modelUrl: 'https://huggingface.co/NikolayKozloff/falcon-7b-GGUF',
    downloadUrl:
      'https://huggingface.co/NikolayKozloff/falcon-7b-GGUF/resolve/main/falcon-7b-Q4_0-GGUF.gguf',
    sha256: '',
  },
  {
    id: 'example-cat-anim',
    name: 'Example Cute Cat Animation',
    provider: 'giphy',
    licenses: [LicenseType.Academic, LicenseType.Commercial, LicenseType.Other],
    description: 'This is a test file (gif) for testing download behavior.',
    fileSize: 0.03, // 3060203 bytes
    fileName: 'cute-cat-anim.gif',
    downloadUrl: 'https://media.giphy.com/media/04uUJdw2DliDjsNOZV/giphy.gif',
  },
]

export default models
