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
  const checkHasDownload = (modelId: string): boolean => {
    // @TODO We should find a way to check the last saved path for file existence
    const data = localStorage.getItem(ITEM_TEXT_MODELS)
    const list = data ? JSON.parse(data) : []
    const matched = list.find((item: string) => item === modelId)
    return matched
  }
  const onDownloadComplete = (modelId: string) => {
    const data = localStorage.getItem(ITEM_TEXT_MODELS)
    const list = data ? JSON.parse(data) : []
    list.push(modelId)
    const arrayStr = JSON.stringify(list)
    localStorage.setItem(ITEM_TEXT_MODELS, arrayStr)
  }

  const cards = data?.map(item => {
    return (
      <ModelCard
        key={item.id}
        id={item.id}
        name={item.name}
        description={item.description}
        fileSize={item.fileSize}
        provider={item.provider}
        license={item.license}
        downloadUrl={item.downloadUrl}
        saveToPath={modelPath}
        fileName={item.fileName}
        isLoaded={currentTextModel === item.id}
        initialHasDownload={checkHasDownload(item.id)}
        onSelectModel={onSelectTextModel}
        onDownloadComplete={onDownloadComplete}
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
