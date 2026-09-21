package com.precog.data

import android.content.Context
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.Base64
import java.security.KeyStore
import java.security.SecureRandom
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec

/**
 * Produces the SQLCipher passphrase for the local database.
 *
 * The passphrase is 32 random bytes generated once on first launch. It is never stored in
 * the clear: it is sealed with an AES-GCM key held in the Android Keystore (hardware-backed
 * where the device provides it) and the sealed blob lives in private SharedPreferences.
 * Nothing leaves the device and there is no recovery path — wiping the key wipes the data,
 * which is the intended behaviour for the Settings "delete everything" control.
 */
object DatabaseKeyProvider {

    private const val PREFS = "precog_key_store"
    private const val KEY_BLOB = "sealed_passphrase"
    private const val KEYSTORE_ALIAS = "precog_db_key"
    private const val ANDROID_KEYSTORE = "AndroidKeyStore"
    private const val TRANSFORM = "AES/GCM/NoPadding"
    private const val IV_BYTES = 12
    private const val TAG_BITS = 128
    private const val PASSPHRASE_BYTES = 32

    fun passphrase(context: Context): ByteArray {
        val prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        val existing = prefs.getString(KEY_BLOB, null)
        if (existing != null) {
            runCatching { return unseal(Base64.decode(existing, Base64.NO_WRAP)) }
            // Keystore key lost (device restore, key invalidation). The old ciphertext is
            // unrecoverable, so start clean rather than failing to open.
            prefs.edit().remove(KEY_BLOB).apply()
        }
        val fresh = ByteArray(PASSPHRASE_BYTES).also { SecureRandom().nextBytes(it) }
        prefs.edit().putString(KEY_BLOB, Base64.encodeToString(seal(fresh), Base64.NO_WRAP)).apply()
        return fresh
    }

    fun destroy(context: Context) {
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit().clear().apply()
        runCatching {
            KeyStore.getInstance(ANDROID_KEYSTORE).apply { load(null) }.deleteEntry(KEYSTORE_ALIAS)
        }
    }

    private fun secretKey(): SecretKey {
        val ks = KeyStore.getInstance(ANDROID_KEYSTORE).apply { load(null) }
        (ks.getEntry(KEYSTORE_ALIAS, null) as? KeyStore.SecretKeyEntry)?.let { return it.secretKey }
        val generator = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, ANDROID_KEYSTORE)
        generator.init(
            KeyGenParameterSpec.Builder(
                KEYSTORE_ALIAS,
                KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT,
            )
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                .setKeySize(256)
                .build()
        )
        return generator.generateKey()
    }

    private fun seal(plain: ByteArray): ByteArray {
        val cipher = Cipher.getInstance(TRANSFORM).apply { init(Cipher.ENCRYPT_MODE, secretKey()) }
        val body = cipher.doFinal(plain)
        return cipher.iv + body
    }

    private fun unseal(blob: ByteArray): ByteArray {
        val iv = blob.copyOfRange(0, IV_BYTES)
        val body = blob.copyOfRange(IV_BYTES, blob.size)
        val cipher = Cipher.getInstance(TRANSFORM).apply {
            init(Cipher.DECRYPT_MODE, secretKey(), GCMParameterSpec(TAG_BITS, iv))
        }
        return cipher.doFinal(body)
    }
}
