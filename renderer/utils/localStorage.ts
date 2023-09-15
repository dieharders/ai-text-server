import { IModelConfig } from '@/components/text-model-browser/configs'
import { INSTALLED_TEXT_MODELS } from '@/components/text-model-browser/ModelBrowser'

const getTextModelsList = () => {
  const data = localStorage.getItem(INSTALLED_TEXT_MODELS)
  const modelConfigs = data ? JSON.parse(data) : []
  return modelConfigs
}

const getTextModelConfig = (id: string) => {
  const modelConfigs = getTextModelsList()
  const config = modelConfigs.find((item: IModelConfig) => item.id === id)

  if (!config) {
    console.log('@@ Cannot find text model config data')
    return null
  }

  return config
}

const setTextModelConfig = (newList: Array<IModelConfig>) => {
  const arrayStr = JSON.stringify(newList)
  localStorage.setItem(INSTALLED_TEXT_MODELS, arrayStr)
  return
}

const removeTextModelConfig = (id: string) => {
  const modelConfigs = getTextModelsList()
  const index = modelConfigs.findIndex((item: IModelConfig) => item.id === id)
  if (index === -1) throw Error('Failed to find model config')
  // Remove config from list
  modelConfigs.splice(index, 1)
  setTextModelConfig(modelConfigs)
  return true
}

export { getTextModelsList, getTextModelConfig, setTextModelConfig, removeTextModelConfig }
