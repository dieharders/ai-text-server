export interface IModelCard {
  id: string
  name: string
  provider: string
  license: string
  description: string
  fileSize: number
  fileName: string
  downloadUrl: string
  modelType?: string
}

const models: Array<IModelCard> = [
  {
    id: 'LLaMa-13B-GGML',
    name: 'Llama 13B',
    provider: 'The Bloke',
    license: 'other',
    description:
      "These files are GGML format model files for Meta's LLaMA 13b. GGML files are for CPU + GPU inference using llama.cpp and libraries and UIs which support this format.",
    fileSize: 5.59,
    fileName: 'llama-13b.ggmlv3.q3_K_S.bin',
    downloadUrl:
      'https://huggingface.co/TheBloke/LLaMa-13B-GGML/resolve/main/llama-13b.ggmlv3.q3_K_S.bin',
  },
  {
    id: 'Llama-2-13B-chat-GGML',
    name: 'Llama 2 13B',
    provider: 'The Bloke',
    license: 'other',
    description:
      "These files are GGML format model files for Meta's Llama 2 13B-chat. GGML files are for CPU + GPU inference using llama.cpp and libraries and UIs which support this format. Llama 2 is a collection of pretrained and fine-tuned generative text models ranging in scale from 7 billion to 70 billion parameters. Our fine-tuned LLMs, called Llama-2-Chat, are optimized for dialogue use cases. Llama-2-Chat models outperform open-source chat models on most benchmarks we tested, and in our human evaluations for helpfulness and safety, are on par with some popular closed-source models like ChatGPT and PaLM.",
    fileSize: 5.51,
    fileName: 'llama-2-13b-chat.ggmlv3.q2_K.bin',
    downloadUrl:
      'https://huggingface.co/TheBloke/Llama-2-13B-chat-GGML/resolve/main/llama-2-13b-chat.ggmlv3.q2_K.bin',
  },
  {
    id: 'Wizard-Vicuna-13B-Uncensored-GGML',
    name: 'Wizard Vicuna 13B Uncensored',
    provider: 'The Bloke',
    license: 'other',
    description:
      "These files are GGML format model files for Eric Hartford's Wizard-Vicuna-13B-Uncensored. GGML files are for CPU + GPU inference using llama.cpp and libraries and UIs which support this format.",
    fileSize: 5.43,
    fileName: 'Wizard-Vicuna-13B-Uncensored.ggmlv3.q2_K.bin',
    downloadUrl:
      'https://huggingface.co/TheBloke/Wizard-Vicuna-13B-Uncensored-GGML/resolve/main/Wizard-Vicuna-13B-Uncensored.ggmlv3.q2_K.bin',
  },
  {
    id: 'redpajama-3b-ggml',
    name: 'RedPajama 3B',
    provider: 'Together',
    license: 'apache-2.0',
    description:
      'RedPajama is fine-tuned for Chat conversation. It was developed by Together and leaders from the open-source AI community. The training was done as part of the INCITE 2023 project on Scalable Foundation Models. Req: >=16GB of CPU.',
    fileSize: 1.57,
    fileName: 'RedPajama INCITE Chat 3B.bin',
    downloadUrl:
      'https://huggingface.co/rustformers/redpajama-3b-ggml/resolve/main/RedPajama-INCITE-Base-3B-v1-q4_0.bin',
  },
  {
    id: 'orca_mini_7B-GGML',
    name: 'Orca Mini 7B',
    provider: 'The Bloke',
    license: 'MIT',
    description:
      'An Uncensored LLaMA-7b model trained on explain tuned datasets, created using Instructions and Input from WizardLM, Alpaca & Dolly-V2 datasets and applying Orca Research Paper dataset construction approaches. Req: >=16GB of CPU.',
    fileSize: 4.21,
    fileName: 'orca-mini-v2_7b.ggmlv3.q5_K_M.bin',
    downloadUrl:
      'https://huggingface.co/TheBloke/orca_mini_7B-GGML/resolve/main/orca-mini-v2_7b.ggmlv3.q5_K_M.bin',
  },
  {
    id: 'example_cat_anim',
    name: 'Example Cute Cat Animation',
    provider: 'giphy',
    license: 'other',
    description: 'This is a test file (gif) for testing download behavior.',
    fileSize: 0.03,
    fileName: 'cute-cat-anim.gif',
    downloadUrl: 'https://media.giphy.com/media/04uUJdw2DliDjsNOZV/giphy.gif',
  },
]

export default models
