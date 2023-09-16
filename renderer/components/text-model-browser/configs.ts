export interface IModelConfig {
  id: string
  savePath: string
  numTimesRun: number
  isFavorited: boolean
  modified: string
  size: number
  promptTemplate?: string
  tokenizerPath?: string
  endByte?: number // allow to resume from last byte window
}

export interface IConfigProps {
  modelId: string
  savePath: string
  modified: string
  size: number
}

const createConfig = ({ modelId, savePath, modified, size }: IConfigProps) => {
  const defaultConfig: IModelConfig = {
    id: modelId,
    savePath: savePath || '',
    numTimesRun: 0,
    isFavorited: false,
    modified: modified || '',
    size: size || 0,
  }

  return defaultConfig
}

export default createConfig
