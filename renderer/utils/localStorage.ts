import { IModelConfig } from '@/components/text-model-browser/configs'
import { INSTALLED_TEXT_MODELS } from '@/components/text-model-browser/ModelBrowser'

const getTextModelsList = (): Array<IModelConfig> => {
  const data = localStorage.getItem(INSTALLED_TEXT_MODELS)
  const modelConfigs = data ? JSON.parse(data) : []
  return modelConfigs
}

const getTextModelConfig = (id: string) => {
  const modelConfigs = getTextModelsList()
  const config = modelConfigs.find((item: IModelConfig) => item.id === id)

  if (!config) {
    console.log('[localStorage] Cannot find text model config data')
    return undefined
  }

  return config
}

const setTextModelConfigList = (newList: Array<IModelConfig>) => {
  const arrayStr = JSON.stringify(newList)
  localStorage.setItem(INSTALLED_TEXT_MODELS, arrayStr)
  return
}

const setUpdateTextModelConfig = (id: string, data: any) => {
  const list = getTextModelsList()
  const match = list.findIndex(item => item.id === id)
  let newList
  if (match === -1) {
    list.push(data)
    newList = list
  } else newList = list.map(item => (item.id === id ? { ...item, ...data } : item))

  setTextModelConfigList(newList)
  return true
}

const removeTextModelConfig = (id: string) => {
  const modelConfigs = getTextModelsList()
  const index = modelConfigs.findIndex((item: IModelConfig) => item.id === id)
  if (index === -1) {
    console.log('[localStorage] Failed to find model config.')
    return false
  }
  // Remove config from list
  modelConfigs.splice(index, 1)
  setTextModelConfigList(modelConfigs)
  return true
}

export {
  getTextModelsList,
  getTextModelConfig,
  setTextModelConfigList,
  removeTextModelConfig,
  setUpdateTextModelConfig,
}
