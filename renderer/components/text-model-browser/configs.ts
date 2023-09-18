export interface IModelConfig {
  id: string
  savePath: string
  numTimesRun: number
  isFavorited: boolean
  validation: 'success' | 'fail' | 'none'
  modified: string
  size: number
  endByte?: number // allow to resume from last byte downloaded
  // promptTemplate?: @TODO string put this in the "model info card" type
  tokenizerPath?: string
}

export interface IConfigProps {
  modelId: string
  savePath: string
  modified: string
  validation: 'success' | 'fail' | 'none'
  size: number
  endByte?: number
  tokenizerPath?: string
}

// This is the model info saved to persistent memory
const createConfig = ({
  modelId,
  savePath,
  modified,
  size,
  validation,
  endByte,
  tokenizerPath,
}: IConfigProps): IModelConfig => {
  const defaultConfig: IModelConfig = {
    id: modelId,
    savePath: savePath || '',
    numTimesRun: 0,
    isFavorited: false,
    validation,
    modified: modified || '',
    size: size || 0,
    endByte,
    tokenizerPath,
  }

  return defaultConfig
}

export default createConfig
