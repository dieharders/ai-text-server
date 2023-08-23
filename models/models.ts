interface IModelCard {
  id: string
  name: string
  provider: string
  license: string
  description: string
  fileSize: number
  fileName: string
  downloadUrl: string
}

// @TODO Add links for rest of models and put in external file. Make this an array of model objects.
const models: Array<IModelCard> = [
  {
    id: 'Llama1_13b',
    name: 'Llama 1 13B',
    provider: 'Meta',
    license: '??',
    description: 'Open source LLM model released and trained by Meta.',
    fileSize: 1,
    fileName: 'llama-13b.ggmlv3.q3_K_S.bin',
    downloadUrl:
      'https://huggingface.co/TheBloke/LLaMa-13B-GGML/resolve/main/llama-13b.ggmlv3.q3_K_S.bin',
  },
  {
    id: 'Llama2_13B',
    name: 'Llama 2 13B',
    provider: 'Meta',
    license: '??',
    description: '',
    fileSize: 1,
    fileName: 'gptq_model-4bit-32g.safetensors',
    downloadUrl: '',
  },
  {
    id: 'WizardVicuna',
    name: 'WizardVicuna Uncensored',
    provider: 'The Bloke',
    license: '??',
    description: '',
    fileSize: 1,
    fileName: 'Wizard Vicuna 7B Uncensored.bin',
    downloadUrl: '',
  },
  {
    id: 'RedPajama3B',
    name: 'RedPajama 3B',
    provider: '??',
    license: '??',
    description: '',
    fileSize: 1,
    fileName: 'RedPajama INCITE Chat 3B.bin',
    downloadUrl: '',
  },
  {
    id: 'OrcaMini7BV2',
    name: 'Orca Mini V2 7B',
    provider: '??',
    license: '??',
    description: '',
    fileSize: 1,
    fileName: 'Orca Mini V2 7B.bin',
    downloadUrl: '',
  },
]

export default models
