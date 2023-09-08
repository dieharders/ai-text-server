use crate::{
    // config::{self, ConfigKey},
    model,
    // path::{read_directory, DirectoryState, FileInfo},
    utils::kv_bucket::remove_data,
};

// static LOAD_MODIFIER: u64 = 3600 * 24;

#[tauri::command]
pub async fn delete_model_file(
    model_integrity_bucket_state: tauri::State<'_, model::integrity::State>,
    // model_stats_bucket_state: tauri::State<'_, model::stats::State>,
    model_download_progress_state: tauri::State<'_, model::downloader::State>,
    // model_config_state: tauri::State<'_, model::config::State>,
    path: &str,
) -> Result<(), String> {
    tokio::try_join!(
        async {
            tokio::fs::remove_file(&path)
                .await
                .map_err(|e| format!("{}", e))
        },
        remove_data(&model_integrity_bucket_state.0, &path),
        // remove_data(&model_config_state.0, &path),
        // remove_data(&model_stats_bucket_state.0, &path),
        remove_data(
            &model_download_progress_state.download_progress_bucket,
            &path
        )
    )?;

    Ok(())
}
