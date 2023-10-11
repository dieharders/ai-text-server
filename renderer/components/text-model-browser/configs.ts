export enum EValidationState {
  Success = 'success',
  Fail = 'fail',
  None = 'none',
}

export interface IModelConfig {
  id: string
  savePath: string
  numTimesRun: number
  isFavorited: boolean
  validation: EValidationState
  modified: string
  size: number
  endChunk?: number // allow to resume from last byte downloaded
  progress?: number
  tokenizerPath?: string
  checksum: string
}

// This is the model info saved to persistent memory
const createConfig = ({
  modelId,
  savePath,
  modified,
  size,
  validation,
  endChunk,
  progress,
  tokenizerPath,
  checksum,
}: any): IModelConfig => {
  const defaultConfig: IModelConfig = {
    id: modelId,
    savePath: savePath || '',
    numTimesRun: 0,
    isFavorited: false,
    validation: validation || EValidationState.None,
    modified: modified || '',
    size: size || 0,
    endChunk: endChunk || 0,
    progress: progress || 0,
    tokenizerPath: tokenizerPath || '',
    checksum: checksum || '',
  }

  return defaultConfig
}

export default createConfig
