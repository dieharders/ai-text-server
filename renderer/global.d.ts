type THandler = (event: any, msg: any) => void
declare global {
  interface Window {
    electron: {
      message: {
        send: (payload: any) => void
        on: (handler: THandler) => void
        off: (handler: THandler) => void
      }
      api: (methodName: string, options?: any) => Promise<any>
    }
  }
}
export {}
