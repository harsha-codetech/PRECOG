package com.precog.ui

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Insights
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.filled.Timeline
import androidx.compose.material.icons.outlined.Home
import androidx.compose.material3.Icon
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.NavigationBarItemDefaults
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavDestination.Companion.hierarchy
import androidx.navigation.NavGraph.Companion.findStartDestination
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.precog.ui.screens.HistoryScreen
import com.precog.ui.screens.HomeScreen
import com.precog.ui.screens.OnboardingScreen
import com.precog.ui.screens.PatternsScreen
import com.precog.ui.screens.SessionDetailScreen
import com.precog.ui.screens.SettingsScreen
import com.precog.ui.theme.Accent
import com.precog.ui.theme.Ink
import com.precog.ui.theme.PrecogTheme
import com.precog.ui.theme.Surface1
import com.precog.ui.theme.TextSecondary
import com.precog.ui.vm.PrecogViewModel

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            PrecogTheme {
                val vm: PrecogViewModel = viewModel()
                val onboarded by vm.onboardingComplete.collectAsState()

                when (onboarded) {
                    // Null means the stored flag has not been read back yet. Showing onboarding
                    // during that gap would flash the consent flow at people who already gave it.
                    null -> Box(Modifier.fillMaxSize())
                    false -> OnboardingScreen(vm) { vm.completeOnboarding() }
                    true -> PrecogApp(vm)
                }
            }
        }
    }
}

private enum class Tab(
    val route: String,
    val label: String,
    val icon: ImageVector,
) {
    HOME("home", "Today", Icons.Outlined.Home),
    HISTORY("history", "History", Icons.Filled.Timeline),
    PATTERNS("patterns", "Patterns", Icons.Filled.Insights),
    SETTINGS("settings", "Settings", Icons.Filled.Settings),
}

@Composable
private fun PrecogApp(vm: PrecogViewModel) {
    val nav = rememberNavController()
    val backStack by nav.currentBackStackEntryAsState()
    val current = backStack?.destination

    // The session detail is a push, not a tab, so the bar hides there and the back arrow
    // inside the screen is the only way out — one way back, not two.
    val onDetail = current?.route?.startsWith("session/") == true

    Scaffold(
        containerColor = Ink,
        bottomBar = {
            if (!onDetail) {
                NavigationBar(containerColor = Surface1) {
                    Tab.entries.forEach { tab ->
                        val selected = current?.hierarchy?.any { it.route == tab.route } == true
                        NavigationBarItem(
                            selected = selected,
                            onClick = {
                                nav.navigate(tab.route) {
                                    popUpTo(nav.graph.findStartDestination().id) { saveState = true }
                                    launchSingleTop = true
                                    restoreState = true
                                }
                            },
                            icon = { Icon(tab.icon, contentDescription = null) },
                            label = { Text(tab.label) },
                            colors = NavigationBarItemDefaults.colors(
                                selectedIconColor = Accent,
                                selectedTextColor = Accent,
                                unselectedIconColor = TextSecondary,
                                unselectedTextColor = TextSecondary,
                                indicatorColor = Color.Transparent,
                            ),
                        )
                    }
                }
            }
        },
    ) { insets ->
        NavHost(
            navController = nav,
            startDestination = Tab.HOME.route,
            modifier = Modifier.padding(insets),
        ) {
            composable(Tab.HOME.route) {
                HomeScreen(
                    vm = vm,
                    onOpenSession = { nav.navigate("session/$it") },
                    onOpenPatterns = { nav.navigate(Tab.PATTERNS.route) },
                )
            }
            composable(Tab.HISTORY.route) {
                HistoryScreen(vm) { nav.navigate("session/$it") }
            }
            composable(Tab.PATTERNS.route) { PatternsScreen(vm) }
            composable(Tab.SETTINGS.route) { SettingsScreen(vm) }
            composable("session/{id}") { entry ->
                val id = entry.arguments?.getString("id")?.toLongOrNull() ?: -1L
                SessionDetailScreen(vm, id) { nav.popBackStack() }
            }
        }
    }
}
