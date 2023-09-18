'use client'

import { Dispatch, SetStateAction } from 'react'
import ModelCard from './ModelCard'
import { IModelCard } from '@/models/models'
import createConfig, { IConfigProps } from './configs'
import { getTextModelConfig, getTextModelsList, setTextModelConfig } from '@/utils/localStorage'

interface IProps {
  data: Array<IModelCard>
  currentTextModel: string
  savePath: string
  setCurrentTextModel: Dispatch<SetStateAction<string>>
}

// LocalStorage keys
export const INSTALLED_TEXT_MODELS = 'installed-text-models'
export const ITEM_CURRENT_MODEL = 'current-text-model'

/**
 * List of curated text inference models
 */
const ModelBrowser = ({ data, currentTextModel, savePath, setCurrentTextModel }: IProps) => {
  // Handlers
  const onSelectTextModel = (val: string) => {
    console.log('@@ Set current text model:', val)
    if (val) {
      setCurrentTextModel(val)
      localStorage.setItem(ITEM_CURRENT_MODEL, val)
    }
  }
  const onDownloadComplete = () => {
    console.log('@@ [Downloader] File saved successfully!')
  }

  // Create new entry for the installed model and record the install path.
  const setModelConfig = (props: IConfigProps) => {
    // Get the stored list of installed configs
    const list = getTextModelsList()
    // Create new config
    const config = createConfig(props)
    // Store new entry
    list.push(config)
    setTextModelConfig(list)
    console.log('@@ [localStorage] Created new config:', config)
  }

  // Components
  // @TODO Put in useMemo()
  const cards = data?.map(item => {
    return (
      <ModelCard
        key={item.id}
        modelCard={item}
        saveToPath={savePath}
        isLoaded={currentTextModel === item.id}
        getModelConfig={() => {
          // Look up the installed model.
          return getTextModelConfig(item.id)
        }}
        setModelConfig={setModelConfig}
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
