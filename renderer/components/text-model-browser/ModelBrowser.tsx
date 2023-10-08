'use client'

import { Dispatch, SetStateAction, useCallback, useMemo } from 'react'
import ModelCard from './ModelCard'
import { IModelCard } from '@/models/models'
import createConfig from './configs'
import { getTextModelConfig, setUpdateTextModelConfig } from '@/utils/localStorage'

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
  const onSelectTextModel = useCallback(
    (id: string) => {
      console.log('[UI] Set current text model:', id)
      if (id) {
        setCurrentTextModel(id)
        localStorage.setItem(ITEM_CURRENT_MODEL, id)
      }
    },
    [setCurrentTextModel],
  )
  const onDownloadComplete = useCallback(() => {
    console.log('[UI] [Downloader] File saved successfully!')
  }, [])

  // Create new entry for the installed model and record the install path.
  const setModelConfig = (props: any) => {
    // Create new config
    const config = createConfig(props)
    // Store/Overwrite with new entry
    setUpdateTextModelConfig(config.id, config)
    console.log('[UI] [localStorage] Created new config:', config)
  }

  // Components
  const cards = useMemo(() => {
    return data?.map(item => {
      return (
        <ModelCard
          key={item.id}
          modelCard={item}
          saveToPath={savePath}
          isLoaded={currentTextModel === item.id}
          loadModelConfig={() => {
            try {
              // Look up the installed model.
              return getTextModelConfig(item.id)
            } catch (err) {
              // Error cant load model. `localStorage` possibly undefined.
              return undefined
            }
          }}
          saveModelConfig={setModelConfig}
          onSelectModel={onSelectTextModel}
          onDownloadComplete={onDownloadComplete}
        ></ModelCard>
      )
    })
  }, [currentTextModel, data, onDownloadComplete, onSelectTextModel, savePath])

  return (
    <div className="z-5 mt-16 flex h-full w-full flex-col justify-center gap-8 rounded-xl border-b border-gray-300 bg-gray-200 p-6 backdrop-blur-sm dark:border-neutral-800 dark:bg-zinc-800/30 lg:mb-0 lg:mt-52 lg:w-10/12 2xl:w-3/6">
      {cards}
    </div>
  )
}

export default ModelBrowser
