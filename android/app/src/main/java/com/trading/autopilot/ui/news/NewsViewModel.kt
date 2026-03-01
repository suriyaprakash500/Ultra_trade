package com.trading.autopilot.ui.news

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.trading.autopilot.data.model.NewsAnalysis
import com.trading.autopilot.data.repository.TradingRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class NewsUiState(
    val isLoading: Boolean = false,
    val error: String? = null,
    val news: List<NewsAnalysis> = emptyList()
)

@HiltViewModel
class NewsViewModel @Inject constructor(
    private val repository: TradingRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(NewsUiState())
    val uiState: StateFlow<NewsUiState> = _uiState.asStateFlow()

    init { refresh() }

    fun refresh() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)
            repository.getNews().onSuccess { news ->
                _uiState.value = _uiState.value.copy(isLoading = false, news = news)
            }.onFailure { e ->
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = e.message ?: "Failed to load news"
                )
            }
        }
    }
}
