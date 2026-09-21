package com.precog.engine.math

import kotlin.math.abs
import kotlin.math.sqrt

/** Dense operations for the small (<= 8 x 8) matrices this pipeline needs. */
object Matrix {

    /** Sample covariance of [rows], each row a d-dimensional observation. */
    fun covariance(rows: List<DoubleArray>): Array<DoubleArray> {
        val n = rows.size
        val d = rows.first().size
        val mu = DoubleArray(d)
        for (r in rows) for (j in 0 until d) mu[j] += r[j]
        for (j in 0 until d) mu[j] /= n
        val cov = Array(d) { DoubleArray(d) }
        for (r in rows) {
            for (i in 0 until d) {
                val di = r[i] - mu[i]
                for (j in i until d) {
                    val v = di * (r[j] - mu[j])
                    cov[i][j] += v
                    if (i != j) cov[j][i] += v
                }
            }
        }
        val denom = (n - 1).coerceAtLeast(1).toDouble()
        for (i in 0 until d) for (j in 0 until d) cov[i][j] /= denom
        return cov
    }

    /**
     * Eigendecomposition of a real symmetric matrix by the cyclic Jacobi method.
     * Returns eigenvalues sorted descending, with [vectors] holding the matching
     * eigenvectors as columns.
     */
    fun symmetricEigen(input: Array<DoubleArray>, maxSweeps: Int = 60): Eigen {
        val n = input.size
        val a = Array(n) { input[it].copyOf() }
        val v = Array(n) { i -> DoubleArray(n) { j -> if (i == j) 1.0 else 0.0 } }

        repeat(maxSweeps) {
            var off = 0.0
            for (p in 0 until n - 1) for (q in p + 1 until n) off += a[p][q] * a[p][q]
            if (off < 1e-18) return@repeat

            for (p in 0 until n - 1) {
                for (q in p + 1 until n) {
                    if (abs(a[p][q]) < 1e-15) continue
                    val theta = (a[q][q] - a[p][p]) / (2.0 * a[p][q])
                    val t = if (theta >= 0) 1.0 / (theta + sqrt(1.0 + theta * theta))
                            else -1.0 / (-theta + sqrt(1.0 + theta * theta))
                    val c = 1.0 / sqrt(1.0 + t * t)
                    val s = t * c

                    for (k in 0 until n) {
                        val akp = a[k][p]; val akq = a[k][q]
                        a[k][p] = c * akp - s * akq
                        a[k][q] = s * akp + c * akq
                    }
                    for (k in 0 until n) {
                        val apk = a[p][k]; val aqk = a[q][k]
                        a[p][k] = c * apk - s * aqk
                        a[q][k] = s * apk + c * aqk
                    }
                    for (k in 0 until n) {
                        val vkp = v[k][p]; val vkq = v[k][q]
                        v[k][p] = c * vkp - s * vkq
                        v[k][q] = s * vkp + c * vkq
                    }
                }
            }
        }

        val values = DoubleArray(n) { a[it][it] }
        val order = values.indices.sortedByDescending { values[it] }
        val sortedValues = DoubleArray(n) { values[order[it]] }
        val sortedVectors = Array(n) { row -> DoubleArray(n) { col -> v[row][order[col]] } }
        return Eigen(sortedValues, sortedVectors)
    }

    data class Eigen(val values: DoubleArray, val vectors: Array<DoubleArray>) {
        /** Column [k] as a vector. */
        fun component(k: Int): DoubleArray = DoubleArray(vectors.size) { vectors[it][k] }

        override fun equals(other: Any?) = this === other
        override fun hashCode() = System.identityHashCode(this)
    }
}
