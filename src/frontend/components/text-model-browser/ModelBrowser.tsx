'use client'

import { Dispatch, SetStateAction } from 'react'
import ModelCard from './ModelCard'
import { IModelCard } from '../../../../models/models'

interface IProps {
  data: Array<IModelCard>
  currentTextModel: string
  modelPath: string
  ITEM_CURRENT_MODEL: string
  ITEM_TEXT_MODELS: string
  setCurrentTextModel: Dispatch<SetStateAction<string>>
}

/**
 * List of curated text inference models
 */
const ModelBrowser = ({
  data,
  currentTextModel,
  modelPath,
  ITEM_CURRENT_MODEL,
  ITEM_TEXT_MODELS,
  setCurrentTextModel,
}: IProps) => {
  // Handlers
  const onSelectTextModel = (val: string) => {
    console.log('@@ Set current text model:', val)
    if (val) {
      setCurrentTextModel(val)
      localStorage.setItem(ITEM_CURRENT_MODEL, val)
    }
  }
  /**
   * Look up the installed model.
   */
  const getModelConfig = (modelId: string): boolean => {
    // @TODO Check the last saved path for file existence before continuing
    const data = localStorage.getItem(ITEM_TEXT_MODELS)
    const list = data ? JSON.parse(data) : []
    const matched = list.find((item: string) => item === modelId)
    return matched
  }
  /**
   * Create new entry for model and record the install path.
   */
  const setModelConfig = (modelId: string, modelPath: string) => {
    const data = localStorage.getItem(ITEM_TEXT_MODELS)
    const list = data ? JSON.parse(data) : []
    list.push(modelId)
    const arrayStr = JSON.stringify(list)
    localStorage.setItem(ITEM_TEXT_MODELS, arrayStr)
    // @TODO Record installed modelPath as object [id]: {path: '/installed/path'}
    console.log('@@ downloaded to:', modelPath)
  }

  // @TODO Put in useMemo()
  const cards = data?.map(item => {
    return (
      <ModelCard
        key={item.id}
        modelCard={item}
        saveToPath={modelPath}
        isLoaded={currentTextModel === item.id}
        getModelConfig={() => {
          return getModelConfig(item.id)
        }}
        setModelConfig={() => setModelConfig(item.id, modelPath)}
        onSelectModel={onSelectTextModel}
      ></ModelCard>
    )
  })

  return (
    <div className="z-5 mt-16 flex h-full w-full flex-col justify-center gap-8 rounded-xl border-b border-gray-300 bg-gray-200 p-6 backdrop-blur-sm dark:border-neutral-800 dark:bg-zinc-800/30 lg:mb-0 lg:mt-52 lg:w-10/12 2xl:w-3/6">
      {cards}
    </div>
  )
}

export default ModelBrowser
