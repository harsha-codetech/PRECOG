package com.precog.data.db

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase
import com.precog.data.DatabaseKeyProvider
import net.zetetic.database.sqlcipher.SupportOpenHelperFactory

@Database(
    entities = [
        ScrollEventEntity::class,
        FeatureWindowEntity::class,
        SessionEntity::class,
        BaselineCellEntity::class,
    ],
    version = 1,
    exportSchema = false,
)
abstract class PrecogDatabase : RoomDatabase() {
    abstract fun scrollEvents(): ScrollEventDao
    abstract fun featureWindows(): FeatureWindowDao
    abstract fun sessions(): SessionDao
    abstract fun baselines(): BaselineDao

    companion object {
        private const val DB_NAME = "precog.db"

        @Volatile private var instance: PrecogDatabase? = null

        fun get(context: Context): PrecogDatabase = instance ?: synchronized(this) {
            instance ?: build(context.applicationContext).also { instance = it }
        }

        private fun build(context: Context): PrecogDatabase {
            System.loadLibrary("sqlcipher")
            val passphrase = DatabaseKeyProvider.passphrase(context)
            val factory = SupportOpenHelperFactory(passphrase)
            return Room.databaseBuilder(context, PrecogDatabase::class.java, DB_NAME)
                .openHelperFactory(factory)
                .fallbackToDestructiveMigration()
                .build()
        }

        /** Used by the "delete everything" control in Settings. */
        fun wipe(context: Context) {
            synchronized(this) {
                instance?.close()
                instance = null
                context.deleteDatabase(DB_NAME)
                DatabaseKeyProvider.destroy(context)
            }
        }
    }
}
