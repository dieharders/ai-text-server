'use client'

import { Dispatch, SetStateAction, useCallback, useEffect, useState } from 'react'
import ModelCard from './ModelCard'
import { IModelCard } from '@/models/models'
import createConfig, { IModelConfig } from './configs'
import { getTextModelConfig, setUpdateTextModelConfig } from '@/utils/localStorage'

interface IProps {
  data: Array<IModelCard>
  currentTextModel: string
  setCurrentTextModel: Dispatch<SetStateAction<string>>
  loadTextModelAction: (payload: {
    modelId: string
    pathToModel: string
    textModelConfig: any
  }) => void
}

// LocalStorage keys
export const INSTALLED_TEXT_MODELS = 'installed_text_models'
export const ITEM_CURRENT_MODEL = 'current_text_model'

/**
 * List of curated text inference models
 */
const ModelBrowser = ({
  data,
  currentTextModel,
  setCurrentTextModel,
  loadTextModelAction,
}: IProps) => {
  const [runOnce, setRunOnce] = useState(false)
  // Handlers
  const onSelectTextModel = useCallback(
    (id: string) => {
      console.log('[UI] Set current text model:', id)
      // Load save path from stored config
      const storedConfig = getTextModelConfig(id)
      const savePath = storedConfig?.savePath
      if (id && savePath) {
        setCurrentTextModel(id)
        // Tell backend which model to load
        const payload = { modelId: id, pathToModel: savePath, textModelConfig: storedConfig }
        loadTextModelAction(payload)
        localStorage.setItem(ITEM_CURRENT_MODEL, id)
      } else console.log('[UI] Error: No id or savePath')
    },
    [loadTextModelAction, setCurrentTextModel],
  )
  const onDownloadComplete = useCallback((success: boolean) => {
    if (success) console.log('[UI] File saved successfully!')
    else console.log('[UI] Error: File failed to save')
  }, [])

  // Create new entry for the installed model and record the install path.
  const setModelConfig = (props: IModelConfig) => {
    // Create new config
    const config = createConfig(props)
    // Store/Overwrite with new entry
    setUpdateTextModelConfig(config.id, config)
    console.log('[UI] Created new config:', config)
  }

  // Components
  const [cards, setCards] = useState<JSX.Element[] | null>(null)

  const createCard = useCallback(
    (item: IModelCard) => {
      return (
        <ModelCard
          key={item.id}
          modelCard={item}
          isLoaded={currentTextModel === item.id}
          loadModelConfig={() => {
            try {
              // Look up the installed model if exists
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
    },
    [currentTextModel, onDownloadComplete, onSelectTextModel],
  )

  useEffect(() => {
    if (runOnce || !data) return
    const ref = data.map(createCard)
    setCards(ref)
    setRunOnce(true)
  }, [createCard, data, runOnce])

  return (
    <div className="z-5 mt-16 flex h-full w-full flex-col justify-center gap-8 rounded-xl border-b border-gray-300 bg-gray-200 p-6 backdrop-blur-sm dark:border-neutral-800 dark:bg-zinc-800/30 lg:mb-0 lg:mt-52 lg:w-10/12 2xl:w-3/6">
      {cards}
    </div>
  )
}

export default ModelBrowser
